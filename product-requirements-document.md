# Product Requirements Document (PRD)

**Title:** AI-Powered Discount Strategy Suggestion Agent  
**Date:** 2026-07-15  
**Owner:** Sales Operations  
**Solution Category:** n8n Workflow, AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Sales reps negotiate discounts based on gut feel, risking margin erosion. This solution automatically analyzes customer orders and margin targets from SAP S/4HANA SD and delivers AI-generated, margin-safe discount recommendations directly to reps at the moment they need them.

**Business Need:**  
Sales representatives lack real-time, data-driven guidance when making discounting decisions. Current processes rely on manual lookups, experience, and informal rules — leading to inconsistent discounts, margin leakage, and slower deal closure.

**Product Objectives (Prioritized):**
1. Provide margin-safe discount recommendations to sales reps at order-creation time
2. Retrieve and contextualize live order and pricing data from SAP S/4HANA SD via standard APIs
3. Ensure all recommendations are explainable and traceable to source data

---

## Requirements

### Must-Have Requirements

**R1: Sales Order Data Retrieval**
- **User Story:** As a sales rep, I need the system to automatically pull my customer's open order details from SAP S/4HANA so I receive relevant discount context without manual lookups.
- **Acceptance Criteria:** Given a sales order ID, when the workflow triggers, then order header, line items, customer, and pricing conditions are fetched via the SAP SD OData API.
- **Priority Rank:** 1

**R2: Margin Target Analysis**
- **User Story:** As a sales manager, I need the AI to factor in margin targets and current pricing conditions so that recommended discounts never breach our floor margins.
- **Acceptance Criteria:** Given order data and margin thresholds, when the AI agent runs, then it returns a discount recommendation with margin impact clearly stated.
- **Priority Rank:** 2

**R3: Contextualized Discount Recommendation**
- **User Story:** As a sales rep, I need a concise AI-generated discount recommendation with reasoning so I can confidently negotiate with the customer.
- **Acceptance Criteria:** Given order and pricing data, when the agent completes analysis, then a structured recommendation (suggested discount %, rationale, risk flag) is returned.
- **Priority Rank:** 3

**R4: Workflow Delivery to Sales Rep**
- **User Story:** As a sales rep, I need recommendations delivered through my existing workflow so I don't need to switch tools.
- **Acceptance Criteria:** When the n8n workflow completes, the recommendation is surfaced in the designated output channel (e.g., email, webhook response, or UI notification).
- **Priority Rank:** 4

---

## Solution Architecture

**Architecture Overview:**  
An n8n workflow is triggered by a new or updated sales order event. It fetches order details and pricing conditions from SAP S/4HANA via OData APIs, then passes structured data to a Python-based AI agent hosted on SAP BTP AI Core. The agent reasons over order history, pricing conditions, and margin floor rules, then returns a structured discount recommendation back through the workflow to the sales rep.

**Key Components:**
- **n8n Workflow**: Orchestrates the end-to-end flow — trigger, API calls, agent invocation, and output delivery
- **SAP S/4HANA SD OData APIs**: Source of sales order data, pricing conditions, and rebate information
- **Python AI Agent (SAP BTP AI Core)**: Performs margin analysis and discount reasoning; returns structured recommendations
- **Output Channel**: Delivers the recommendation to the sales rep (webhook, email, or UI)

**Integration Points:**
- SAP S/4HANA Sales Order API (`API_SALES_ORDER_SRV`) — reads order header and items
- SAP S/4HANA Pricing Condition Record API (`API_SLSPRICINGCONDITIONRECORD_SRV`) — reads active discount/pricing conditions
- SAP S/4HANA Pricing Procedure API (`API_SLSPRICINGPROCEDURE_SRV`) — reads pricing logic structure

---

### Automation & Agent Behaviour

**Automation Level:** ML-assisted (AI proposes, human approves)

**Actions the system performs without human approval:**
- Fetch order data from SAP S/4HANA
- Analyze margin targets and pricing conditions
- Generate discount recommendation with rationale

**Actions that require human review or approval:**
- Applying the discount to the sales order (rep decides)

**Model or engine used:** LLM via SAP Generative AI Hub (GPT-4o or equivalent)

**Knowledge & data sources accessed:**
- SAP S/4HANA SD: sales orders, pricing conditions, pricing procedures
- Margin floor rules (configured as agent input parameters)

**Tools or connectors invoked:**
- SAP S/4HANA OData APIs (read-only): order data and pricing conditions
- SAP AI Core LLM endpoint: discount reasoning and recommendation generation

**Guardrails & fail-safes:**
- Agent never writes back to SAP — all recommendations are read-only advisory
- If margin floor would be breached, recommendation is blocked and flagged
- If API call fails, workflow surfaces an error to the rep rather than returning a blank recommendation

---

## Milestones

### M1: Order Data Fetched

- **Description**: Sales order and pricing conditions successfully retrieved from SAP S/4HANA SD
- **Achieved when**: OData API returns order header, items, and active pricing conditions without error
- **Log on achievement**: `M1.achieved: sales order and pricing conditions retrieved from S/4HANA`
- **Log on miss**: `M1.missed: failed to retrieve order or pricing data from S/4HANA`

### M2: Margin Analysis Completed

- **Description**: AI agent has analyzed the order against margin floor targets
- **Achieved when**: Agent returns a margin impact score and determines whether discounting headroom exists
- **Log on achievement**: `M2.achieved: margin analysis completed, headroom calculated`
- **Log on miss**: `M2.missed: margin analysis did not complete or margin data unavailable`

### M3: Discount Recommendation Generated

- **Description**: AI agent produces a structured discount recommendation with rationale
- **Achieved when**: Agent response includes recommended discount %, reasoning, and risk flag
- **Log on achievement**: `M3.achieved: discount recommendation generated successfully`
- **Log on miss**: `M3.missed: agent failed to generate discount recommendation`

### M4: Recommendation Delivered to Sales Rep

- **Description**: Discount recommendation surfaced to the sales rep via the configured output channel
- **Achieved when**: n8n workflow successfully delivers the recommendation payload to the output channel
- **Log on achievement**: `M4.achieved: recommendation delivered to sales rep`
- **Log on miss**: `M4.missed: delivery to output channel failed`
