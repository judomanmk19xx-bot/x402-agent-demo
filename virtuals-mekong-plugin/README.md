# mekong-x402-game — Virtuals G.A.M.E. plugin

G.A.M.E. framework `Function`s for the Mekong x402 pay-per-call API fleet
(Virtuals Protocol). Drop the 5 functions into any Worker's `action_space`.

## 1-command install

```bash
pip install game_sdk mekong-x402-game
export GAME_API_KEY=<your key from https://console.game.virtuals.io/>
```

## Wire into a Worker

```python
from game_sdk.game.worker import Worker
from mekong_x402 import MEKONG_FUNCTIONS

worker = Worker(
    api_key=os.environ["GAME_API_KEY"],
    description="Research assistant with live web + market data tools.",
    get_state_fn=lambda fn_id, space: {"task": "answer the user"},
    action_space=MEKONG_FUNCTIONS,   # <-- 5 x402 functions
)
```

Full example: `example_worker.py` (runs a no-LLM smoke test of one function).

## Functions (5)

| fn_name | What it does | Price after free trial |
|---|---|---|
| `mekong_web_search` | Live web search, deduped + scored | $0.01/call |
| `mekong_brief` | Morning briefing: news + trends + sentiment | $0.05/call |
| `mekong_ai_verdict` | Token safety verdict SAFE/RISKY/SCAM + reasoning | $0.01/call |
| `mekong_enrich` | Company enrichment from domain | $0.02/call |
| `mekong_token_price` | Live token price / mcap / liquidity | $0.001/call |

Each executable returns `(FunctionResultStatus, feedback, info)` per the
`game_sdk` contract. When the free trial is exhausted the function returns
`FAILED` with exact x402 pay instructions in the feedback (plus `pay_to` /
`amount` in `info`) — never silent.

## Payment flow

1. Free daily trial quota per IP, automatic — no key, no signup.
2. Trial exhausted → `X402PaymentRequired` → feedback carries: amount (USDC,
   6 decimals), `payTo`, asset (USDC on Base), network (`eip155:8453`).
3. Sign an x402 `exact`-scheme transfer and retry with `X-PAYMENT` /
   `PAYMENT-SIGNATURE`. JS libs: `@x402/fetch`, `x402-axios`.

## Publish to PyPI (maintainer)

```bash
pip install build twine
python -m build
twine upload dist/*   # package: mekong-x402-game
```

To propose it as an official game-python plugin, open a PR against
`game-by-virtuals/game-python` adding a folder under `plugins/` following
`plugins/plugin_metadata_template.yml` (see `plugin_metadata.yml` here),
per their `CONTRIBUTION_GUIDE.md`.
