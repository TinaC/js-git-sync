# CRITICAL: Initialize telemetry BEFORE importing AI frameworks
from sap_cloud_sdk.aicore import set_aicore_config
from sap_cloud_sdk.core.telemetry import auto_instrument

set_aicore_config()
auto_instrument()

import json
import logging
import os
import uuid

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from agent import SampleAgent
from agent_executor import AgentExecutor
from mcp_tools import get_mcp_tools, set_user_token
from opentelemetry.instrumentation.starlette import StarletteInstrumentor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

_agent_instance = SampleAgent()


class JWTContextMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts JWT token from Authorization header and sets it in context."""

    async def dispatch(self, request, call_next):
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("authorization", "")
        token = None
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

        # Set the token in the context variable
        set_user_token(token)

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear the token after the request
            set_user_token(None)


async def invoke_endpoint(request: Request) -> JSONResponse:
    """Simple /invoke HTTP endpoint for n8n workflow integration.

    Accepts: POST /invoke with body { "message": "...", "context": "..." }
    Returns: { "recommendation": { ... }, "message": "..." }

    The context field should contain the JSON-stringified sales order payload
    built by the n8n 'Prepare Agent Payload' node.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    message = body.get("message", "")
    context = body.get("context", "")

    # Build a combined query including the structured context
    if context:
        query = f"{message}\n\nSales order data:\n{context}"
    else:
        query = message

    if not query.strip():
        return JSONResponse({"error": "message is required"}, status_code=400)

    # Use a per-request context ID so each invocation is independent
    context_id = str(uuid.uuid4())

    # Load MCP tools
    tools = []
    try:
        from mcp_tools import get_user_token
        user_token = get_user_token()
        tools = await get_mcp_tools(user_token=user_token)
    except Exception as e:
        logger.warning("Failed to load MCP tools for /invoke: %s", e)

    response_text = ""
    try:
        async for chunk in _agent_instance.stream(query, context_id, tools=tools):
            if chunk.get("is_task_complete"):
                response_text = chunk.get("content", "")
                break
    except Exception as e:
        logger.exception("Agent stream failed in /invoke")
        return JSONResponse({"error": str(e)}, status_code=500)

    # Try to extract structured recommendation from the response
    recommendation = {}
    try:
        # Agent is prompted to return JSON; find the first JSON object in the response
        import re
        json_match = re.search(r'\{[^{}]*"suggestedDiscountPercent"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            recommendation = json.loads(json_match.group())
    except Exception:
        pass

    return JSONResponse({
        "recommendation": recommendation,
        "message": response_text,
    })


@click.command()
@click.option("--host", default=HOST)
@click.option("--port", default=PORT)
def main(host: str, port: int):
    skill = AgentSkill(
        id="discount-strategy-agent",
        name="discount-strategy-agent",
        description="An AI agent that analyzes SAP S/4HANA sales orders and margin targets to provide contextualized discount strategy recommendations for sales representatives",
        tags=["discount", "strategy", "sales", "s4hana", "pricing"],
        examples=["Recommend a discount for sales order 0000012345 with a 20% margin floor", "What discount can I offer customer C1000 without dropping below 15% margin?"],
    )
    agent_card = AgentCard(
        name="discount-strategy-agent",
        description="An AI agent that analyzes SAP S/4HANA sales orders and margin targets to provide contextualized discount strategy recommendations for sales representatives",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        skills=[skill],
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )
    app = server.build()

    # Mount /invoke endpoint for n8n workflow integration
    from starlette.routing import Mount, Router
    from starlette.applications import Starlette
    invoke_router = Starlette(routes=[Route("/invoke", invoke_endpoint, methods=["POST"])])
    app.mount("/", invoke_router)

    # Add JWT context middleware
    app.add_middleware(JWTContextMiddleware)

    StarletteInstrumentor().instrument_app(app)

    logger.info(f"Starting A2A server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
