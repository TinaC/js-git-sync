# Specification: n8n

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-n8n-workflow.md](../guidelines-n8n-workflow.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [ ] Read the project input (`product-requirements-document.md`, `intent.md`)

## API Specs

The following OData API spec files have been downloaded and are available at:
- `specification/n8n/api-specs/API_SALES_ORDER_SRV.edmx` — SAP S/4HANA Sales Order API (A2X), ORD ID: `sap.s4:apiResource:API_SALES_ORDER_SRV:v1`
  - Key entities: `A_SalesOrder` (header), `A_SalesOrderItem` (line items), `A_SalesOrderItemPrElement` (item pricing elements)
  - Key endpoints:
    - `GET /A_SalesOrder('{SalesOrder}')` — fetch order header by ID (fields: SalesOrder, SoldToParty, TotalNetAmount, TransactionCurrency, PricingDate, CustomerPriceGroup, CustomerGroup)
    - `GET /A_SalesOrder('{SalesOrder}')/to_Item` — fetch all line items (fields: Material, RequestedQuantity, NetAmount, CostAmount, MaterialGroup)
    - `GET /A_SalesOrderItem(SalesOrder='{SalesOrder}',SalesOrderItem='{Item}')/to_PricingElement` — fetch item pricing elements (fields: ConditionType, ConditionRateValue, ConditionCurrency, ConditionAmount, ConditionCategory)
- `specification/n8n/api-specs/API_SLSPRICINGCONDITIONRECORD_SRV.edmx` — SAP S/4HANA Pricing Condition Record API, ORD ID: `sap.s4:apiResource:API_SLSPRICINGCONDITIONRECORD_SRV:v1`
  - Key entities: `A_SlsPrcgConditionRecord`, `A_SlsPrcgCndnRecdValidity`
  - Key endpoint: `GET /A_SlsPrcgCndnRecdValidity?$filter=SoldToParty eq '{customer}' and ConditionType eq 'RB00'` — fetch active discount condition records for a customer

## Workflow: discount-strategy-n8n

### Trigger

- [ ] Add a **Webhook** trigger node named `Sales Order Trigger`
  - Method: POST
  - Path: `/discount-strategy`
  - Expected body payload:
    ```json
    {
      "salesOrderId": "0000012345",
      "marginFloorPercent": 15.0,
      "agentBaseUrl": "https://agent.company.com"
    }
    ```

### Step 1 — Fetch Sales Order from S/4HANA

- [ ] Add an **HTTP Request** node named `Fetch Sales Order`
  - Method: GET
  - URL: `https://your-sap-system.com/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{{ $json.salesOrderId }}')?$expand=to_Item,to_Item/to_PricingElement&$format=json`
  - Authentication: leave unconfigured (user assigns credentials in n8n UI)
  - On error: continue (handled in error branch)

### Step 2 — Validate Order Data

- [ ] Add an **IF** node named `Order Data Valid`
  - Condition: `{{ $json.d.SalesOrder }}` exists and is not empty
  - True branch → proceed to Step 3
  - False branch → proceed to Error Handler

### Step 3 — Fetch Pricing Condition Records

- [ ] Add an **HTTP Request** node named `Fetch Pricing Conditions`
  - Method: GET
  - URL: `https://your-sap-system.com/sap/opu/odata/sap/API_SLSPRICINGCONDITIONRECORD_SRV/A_SlsPrcgCndnRecdValidity?$filter=SoldToParty eq '{{ $json.d.SoldToParty }}'&$format=json`
  - Authentication: leave unconfigured

### Step 4 — Prepare Agent Payload

- [ ] Add a **Code** node named `Prepare Agent Payload`
  - Build a structured JSON payload combining:
    - `salesOrder`: order header fields (SalesOrder, SoldToParty, TotalNetAmount, TransactionCurrency, PricingDate, CustomerPriceGroup, CustomerGroup)
    - `lineItems`: array of items (Material, RequestedQuantity, NetAmount, CostAmount) with their pricing elements (ConditionType, ConditionRateValue, ConditionCurrency)
    - `pricingConditions`: active condition records from Step 3 (ConditionType, ConditionRateValue, ConditionValidityStartDate, ConditionValidityEndDate)
    - `marginFloorPercent`: pass-through from trigger payload
  - Output: `{ agentPayload: { ... } }`

### Step 5 — Invoke AI Discount Agent

- [ ] Add an **HTTP Request** node named `Call Discount Agent`
  - Method: POST
  - URL: `{{ $('Sales Order Trigger').item.json.agentBaseUrl }}/invoke`
  - Body (JSON):
    ```json
    {
      "message": "Analyze this sales order and recommend a discount strategy. Stay within the margin floor.",
      "context": "{{ JSON.stringify($json.agentPayload) }}"
    }
    ```
  - Authentication: leave unconfigured

### Step 6 — Validate Agent Response

- [ ] Add an **IF** node named `Agent Response Valid`
  - Condition: `{{ $json.recommendation }}` exists
  - True branch → proceed to Step 7
  - False branch → proceed to Error Handler

### Step 7 — Format and Return Recommendation

- [ ] Add a **Code** node named `Format Recommendation`
  - Map agent response into a clean output structure:
    ```json
    {
      "salesOrderId": "...",
      "customerId": "...",
      "suggestedDiscountPercent": 5.0,
      "rationale": "...",
      "marginImpact": "...",
      "riskFlag": "low|medium|high",
      "timestamp": "..."
    }
    ```

- [ ] Add a **Respond to Webhook** node named `Return Recommendation`
  - Response body: `{{ JSON.stringify($json) }}`
  - Status code: 200

### Error Handler

- [ ] Add a **Respond to Webhook** node named `Error Response`
  - Response body: `{ "error": "Failed to generate discount recommendation", "details": "{{ $json.error }}" }`
  - Status code: 500
  - Connect from both IF false branches (Order Data Valid and Agent Response Valid)

## Finalize

- [ ] Write workflow JSON to `assets/n8n/workflows/discount-strategy.n8n.json` using the `n8n-workflow` skill
- [ ] Ensure `connections` in JSON reference nodes by `name`, not `id`
- [ ] Validate workflow JSON is well-formed
