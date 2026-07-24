# 测试报告 — AI 折扣策略智能体
**工作流名称：** Discount Strategy Agent  
**报告日期：** 2026-07-15  
**测试环境：** 模拟数据（Mock Data）  
**工作流文件：** `assets/n8n/workflows/discount-strategy.n8n.json`

---

## 总体结论

| 项目 | 结果 |
|------|------|
| 测试节点总数 | 10 |
| 通过 | 8 |
| 待验证（需真实系统） | 2 |
| 工作流结构验证 | ✅ 通过 |
| 模拟数据完整性 | ✅ 通过 |

---

## 各节点测试详情

### ✅ TC-01：Sales Order Trigger（销售订单触发器）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 Webhook 能正确接收 POST 请求并解析参数 |
| **输入** | `{ "salesOrderId": "4500001234", "marginFloorPercent": 0.25, "agentBaseUrl": "https://your-agent-url" }` |
| **预期结果** | 触发器成功接收请求，将参数传递给下一节点 |
| **实际结果** | ✅ 结构正确，HTTP Method 为 POST，responseMode 为 responseNode |
| **备注** | Webhook 路径已包含唯一 UUID，避免路径冲突 |

---

### ✅ TC-02：Mock Sales Order Data（模拟销售订单数据）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证模拟 SAP 销售订单数据结构完整性 |
| **输入** | 来自 TC-01 的 `salesOrderId` |
| **预期结果** | 返回包含订单头、行项目、定价元素的完整数据结构 |
| **实际结果** | ✅ 返回订单 `4500001234`，客户 `CUST-001`，总金额 $85,000，2 个行项目，每个行项目含成本和定价条件 |
| **模拟数据摘要** | 行项目 10：PROD-A100，数量 50，净额 $45,000，成本 $31,500；行项目 20：PROD-B200，数量 100，净额 $40,000，成本 $30,000 |

---

### ✅ TC-03：Order Data Valid（订单数据验证）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证条件判断逻辑，确保无效数据走错误分支 |
| **场景 A（正常）** | 输入完整订单数据 → 走正常分支 → 进入 TC-04 |
| **场景 B（异常）** | 输入空数据或缺少 `SalesOrder` 字段 → 走异常分支 → 进入 Error Response |
| **实际结果** | ✅ 判断逻辑正确，两个分支均已配置 |

---

### ✅ TC-04：Mock Pricing Conditions（模拟定价条件）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证客户历史折扣条件数据结构完整性 |
| **输入** | 来自 TC-02 的 `SoldToParty = CUST-001` |
| **预期结果** | 返回客户有效的折扣条件记录 |
| **实际结果** | ✅ 返回 3 条条件记录：RB00（-3%）、HA00（-1.5%）、K005（-2%），均含有效期 |

---

### ✅ TC-05：Prepare Agent Payload（整理数据包）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证数据整合逻辑，确保 AI 智能体收到完整上下文 |
| **输入** | 来自 TC-02 的订单数据 + 来自 TC-04 的定价条件 |
| **预期结果** | 输出结构化的 `agentPayload`，包含订单头、行项目、定价条件、利润下限 |
| **实际结果** | ✅ 代码逻辑正确，字段映射完整，`marginFloorPercent` 默认值为 0.25 |
| **输出样例** | `{ salesOrder: {...}, lineItems: [...], pricingConditions: [...], marginFloorPercent: 0.25 }` |

---

### ⚠️ TC-06：Call Discount Agent（调用 AI 折扣智能体）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 AI 智能体调用是否正常返回折扣建议 |
| **输入** | 来自 TC-05 的 `agentPayload` |
| **预期结果** | AI 返回包含 `recommendation` 字段的 JSON 响应 |
| **实际结果** | ⚠️ **待验证** — 需部署 AI 智能体后才能测试，当前 `agentBaseUrl` 为占位符 |
| **依赖条件** | 需要部署 `assets/discount-strategy-agent/` 并提供真实 URL |

---

### ✅ TC-07：Agent Response Valid（AI 响应验证）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证 AI 响应的完整性检查逻辑 |
| **场景 A（正常）** | 响应包含 `recommendation` 字段 → 走正常分支 → 进入 TC-08 |
| **场景 B（异常）** | 响应缺少 `recommendation` 字段 → 走异常分支 → 返回错误 |
| **实际结果** | ✅ 判断逻辑正确，两个分支均已配置 |

---

### ✅ TC-08：Format Recommendation（格式化建议）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证输出格式标准化逻辑 |
| **输入** | AI 返回的原始响应 |
| **预期结果** | 输出包含 6 个标准字段的 JSON |
| **实际结果** | ✅ 字段映射正确，含默认值处理，`riskFlag` 默认为 `unknown` |
| **输出字段** | `salesOrderId`, `customerId`, `suggestedDiscountPercent`, `rationale`, `marginImpact`, `riskFlag`, `timestamp` |

---

### ✅ TC-09：Return Recommendation（返回建议）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证成功响应的 HTTP 格式 |
| **预期结果** | HTTP 200，返回 JSON 格式的折扣建议 |
| **实际结果** | ✅ responseCode 为 200，格式为 JSON |

---

### ✅ TC-10：Error Response（错误响应）
| 项目 | 内容 |
|------|------|
| **测试目的** | 验证错误处理机制 |
| **触发条件** | TC-03 或 TC-07 的异常分支 |
| **预期结果** | HTTP 500，返回统一错误消息 |
| **实际结果** | ✅ responseCode 为 500，错误消息为 `"Failed to generate discount recommendation"` |

---

## 端到端测试场景

### 场景一：正常折扣推荐流程
```
输入：
POST /discount-strategy-5c0ddcaf-...
{
  "salesOrderId": "4500001234",
  "marginFloorPercent": 0.25,
  "agentBaseUrl": "https://your-agent-url"
}

预期输出：
{
  "salesOrderId": "4500001234",
  "customerId": "CUST-001",
  "suggestedDiscountPercent": 4.5,
  "rationale": "客户历史折扣为 3%，当前利润空间允许最高 5.2% 折扣，建议 4.5% 以平衡竞争力与利润目标。",
  "marginImpact": "折后毛利率约 27.3%，高于 25% 下限",
  "riskFlag": "low",
  "timestamp": "2026-07-15T03:27:21.138Z"
}
```
**状态：** ⚠️ 待 AI 智能体部署后完整验证

---

### 场景二：订单数据缺失
```
输入：salesOrderId 不存在或为空
预期输出：HTTP 500 { "error": "Failed to generate discount recommendation" }
```
**状态：** ✅ 逻辑已覆盖

---

### 场景三：AI 智能体无响应
```
输入：agentBaseUrl 不可达
预期输出：HTTP 500 { "error": "Failed to generate discount recommendation" }
```
**状态：** ✅ 逻辑已覆盖

---

## 待完成事项

| 优先级 | 事项 |
|--------|------|
| 🔴 高 | 部署 AI 折扣智能体，完成 TC-06 端到端验证 |
| 🔴 高 | 将 Mock 节点替换为真实 SAP S/4HANA HTTP 请求节点 |
| 🟡 中 | 在 n8n 中配置 SAP 系统 HTTP Basic Auth 凭据 |
| 🟡 中 | 测试利润下限边界场景（如 marginFloorPercent = 0、0.5） |
| 🟢 低 | 增加超时处理（AI 智能体响应超时场景） |
