# PR: Add Mekong x402 tools (pay-per-call APIs, no API key)

**Title:** `feat(community): add Mekong x402 tool family`

**Target repo:** `langchain-ai/langchain-community` → `libs/community/langchain_community/tools/mekong/`
**Files:** `__init__.py`, `tool.py`
(Also: register exports in `libs/community/langchain_community/tools/__init__.py`.)

---

## What

7 native LangChain tools + 1 toolkit for the [Mekong x402 fleet](https://api.mekongtradeintel.com/tools/) —
37 pay-per-call APIs on Base (USDC):

- `MekongTaskRouter` — **FREE** task router: plain-language task → top-3 endpoints + curls
- `MekongWebSearch` — live web search ($0.01)
- `MekongTokenPrice` — price/mcap/liquidity ($0.001)
- `MekongAIVerdict` — token safety verdict ($0.01)
- `MekongEnrich` — company enrichment ($0.02)
- `MekongSTT` — speech-to-text ($0.05)
- `MekongBrief` — news+trends+sentiment bundle ($0.05)
- `MekongX402Toolkit` — bundles all 7

```python
from langchain_community.tools.mekong import MekongTaskRouter, MekongWebSearch

MekongTaskRouter().run({"task": "Is this token a honeypot?"})  # free
MekongWebSearch().run({"query": "Ethereum ETF inflows"})        # free trial, then $0.01
```

## Why this belongs in langchain-community

- **Zero-config:** no API keys, no signup, no env vars — every endpoint has a free
  daily trial quota per IP, so the tools work out of the box.
- **Honest paid path:** trial exhausted → `MekongPaymentRequired` with exact price,
  `payTo`, asset, network and the 3-step x402 flow. Never a silent charge.
- **Independently verifiable:** https://api.mekongtradeintel.com/tools/verify —
  one-command script checking 402 paywall shape, CDP `/x402/validate` preflight
  and on-chain settlement from the outside.

## Conventions followed

- `langchain_core.tools.BaseTool` subclasses with `name`, `description`,
  pydantic `args_schema`, `_run(..., run_manager=None)`, docstring examples
  (mirrors `tools/brave_search/tool.py`).
- Only hard deps: `requests`, `pydantic` (both already in community).

## Tested

- All 7 tools instantiate as real `BaseTool` subclasses; free router tool run
  live against production via `.invoke()` (args_schema-validated):
  `task="Is this token a honeypot?"` → `rugcheck` top-1, correct.
- 402 path unit-tested with mocked responses (raises with pay instructions).

## Notes for reviewers

- Nothing to configure by design — x402 means the wallet is the credential.
- Happy to split per-tool or add `langchain-x-mekong` partner-package scaffolding
  if the new integrations path is preferred over `langchain-community`.
