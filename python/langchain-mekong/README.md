# langchain-mekong

LangChain tools for the [Mekong x402 fleet](https://api.mekongtradeintel.com/tools/) — 37 pay-per-call APIs on Base (USDC).

**No signup. No API key. Your wallet is the credential.** Every endpoint has a free daily trial quota, so the tools work out of the box.

## Install

```bash
pip install langchain-mekong
```

## Use

```python
from langchain_mekong import TaskRouterTool, WebSearchTool

# Free: describe a task, get the right endpoints
print(TaskRouterTool().run(task="Is this token a honeypot?"))

# Paid (or free trial): live web search
print(WebSearchTool().run(query="Ethereum ETF inflows"))
```

7 tools: `TaskRouterTool` (free), `WebSearchTool` ($0.01), `TokenPriceTool` ($0.001), `AIVerdictTool` ($0.01), `EnrichTool` ($0.02), `STTTool` ($0.05), `BriefTool` ($0.05).

When the free trial is exhausted, tools raise `X402PaymentRequired` with the exact price, `payTo`, asset, network and the 3-step x402 payment flow. Never a silent charge.

## Verify independently

https://api.mekongtradeintel.com/tools/verify — one-command script checking the 402 paywall shape, CDP `/x402/validate` preflight and on-chain settlement.
