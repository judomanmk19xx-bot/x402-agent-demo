# x402 Agent Demo — token due-diligence agent

A minimal working agent that pays per API call in USDC on Base ([x402](https://www.x402.org)).
**No signup. No API keys.** Your agent pays $0.021 for a full token briefing.

## What it does

One command runs a 3-step pipeline against live pay-per-call endpoints:

| Step | Endpoint | Price/call | What it returns |
|------|----------|-----------|-----------------|
| 1 | `tokenprice` | $0.001 | Live price, market cap, 24h volume, liquidity (DexScreener) |
| 2 | `aiverdict` | $0.01 | Contract security verdict: SAFE/RISKY + risk score + flags |
| 3 | `websearch` | $0.01 | Latest headlines about the token |

Total: **~$0.021 per run**. 40+ more endpoints at https://api.mekongtradeintel.com/pricing

## Quickstart (free trial, 2 minutes)

```bash
npm install
node agent.mjs        # or: npm start
```

No wallet, no signup — a per-IP daily trial quota applies automatically.
Watch for the `trial left` counter in the output.

## Paid mode (real x402 flow)

```bash
cp .env.example .env   # put your Base private key in PRIVATE_KEY
PRIVATE_KEY=0x... node agent.mjs
```

The agent then does the real x402 dance on every call: `402 Payment Required` →
sign a USDC authorization with your wallet → retry with the `X-PAYMENT` header →
`200` with data. All handled by `@x402/fetch`; ~15 lines of integration code.

## How it works

```
agent.mjs --(POST /tokenprice/api/token-price)--> 200 (trial) or 402
                                                      |
                                              402? sign + retry with X-PAYMENT
                                                      |
                                                     200 + data
```

Endpoints used (use the `/api/` URL form — it always works):

- `POST https://api.mekongtradeintel.com/tokenprice/api/token-price` — body `{"chain":"base","address":"0x..."}`
- `POST https://api.mekongtradeintel.com/aiverdict/api/verdict` — body `{"chain":"base","contract":"0x..."}`
- `POST https://api.mekongtradeintel.com/websearch/api/websearch` — body `{"query":"...","num":5}`

## Python

See [`python/`](python/) for framework-ready snippets (trial mode, `requests` only):

- `smolagents_tool.py` — `Tool` subclass for Hugging Face smolagents
- `crewai_tool.py` — `BaseTool` subclass for CrewAI

## Links

- Pricing: https://api.mekongtradeintel.com/pricing
- Tool docs: https://api.mekongtradeintel.com/tools/
- Agent store: https://api.mekongtradeintel.com/tools/store/
- Machine-readable API catalog: https://api.mekongtradeintel.com/tools/mcp-schema.json
- Adopt an endpoint (50/50 revenue share): https://api.mekongtradeintel.com/tools/adopt

## Security note

Never commit a real private key. `.env` is gitignored; only `.env.example` ships.
