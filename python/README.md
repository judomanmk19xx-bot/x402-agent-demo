# mekong-x402 — native LangChain / CrewAI tools for the x402 fleet

37 pay-per-call APIs on Base (USDC). **No signup, no API key** — your wallet is the credential.
Free daily trial quota on every endpoint. Fleet: https://api.mekongtradeintel.com/tools/

## Install

```bash
pip install "mekong-x402[langchain]"   # LangChain tools
pip install "mekong-x402[crewai]"      # CrewAI tools
pip install "mekong-x402[all]"         # both
pip install mekong-x402                # core client only (no frameworks)
```

## Quickstart — LangChain

```python
from mekong_x402.langchain_tools import TaskRouterTool, WebSearchTool, AIVerdictTool

# FREE: ask which endpoint fits, in plain language
print(TaskRouterTool().run(task="Is this token a honeypot?"))

# Paid endpoints: free trial first, then USDC per call
print(WebSearchTool().run(query="Ethereum ETF inflows"))
print(AIVerdictTool().run(query="Is 0xabc... a honeypot?"))
```

## Quickstart — CrewAI

```python
from crewai import Agent, Task, Crew
from mekong_x402.crewai_tools import WebSearchTool, TaskRouterTool

analyst = Agent(
    role="Research Analyst",
    goal="Brief me with live data",
    tools=[TaskRouterTool(), WebSearchTool()],
    backstory="You use pay-per-call tools. No API keys needed.",
)
```

## Available tools

| Tool | Endpoint | Price |
|---|---|---|
| `TaskRouterTool` | `/recommend` — describe a task, get top-3 endpoints | **FREE** |
| `WebSearchTool` | `/websearch` — live web search | $0.01 |
| `TokenPriceTool` | `/tokenprice` — price/mcap/liquidity (chain+address exact) | $0.001 |
| `AIVerdictTool` | `/aiverdict` — SAFE/RISKY/SCAM + reasoning | $0.01 |
| `EnrichTool` | `/enrich` — company data from domain | $0.02 |
| `STTTool` | `/stt` — speech-to-text from audio URL | $0.05 |
| `BriefTool` | `/brief` — news+trends+sentiment bundle | $0.05 |

Same 7 tools exist in both `mekong_x402.langchain_tools` and `mekong_x402.crewai_tools`.

## How payment works

1. Call without payment → free trial quota applies automatically.
2. Trial exhausted → the tool raises **`X402PaymentRequired`** (never a silent charge).
   The exception message carries the exact price, `payTo`, USDC contract, network,
   and the 3-step x402 flow: sign an exact-scheme USDC transfer on Base →
   base64 the payload → retry with the `X-PAYMENT` header.
3. Libraries that automate it: `x402-axios` / `x402-fetch` (npm).

```python
from mekong_x402 import X402PaymentRequired
try:
    WebSearchTool().run(query="...")
except X402PaymentRequired as e:
    print(e)  # exact pay instructions for the operator
```

Verify independently any time: https://api.mekongtradeintel.com/tools/verify
