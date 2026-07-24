# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [ ] Create asset directories: `mkdir -p assets/n8n/workflows/ assets/discount-strategy-agent/`
- [ ] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for every asset
- [ ] Validate all `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [ ] Execute specification/n8n/specification.md (all items)
- [ ] Execute specification/discount-strategy-agent/specification.md (all items)
- [ ] Cross-implementation compatibility check: verify the n8n workflow's agent invocation URL placeholder matches the discount-strategy-agent's expected invoke endpoint; verify the JSON payload shape sent by the n8n workflow matches what the agent's `stream()` method expects; fix any mismatches before proceeding
