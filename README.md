# Mekong x402 — framework plugins

Native 1-command-install plugins that put the Mekong x402 pay-per-call API
fleet inside the agent frameworks where agents actually live.

Fleet: 45 endpoints at https://api.mekongtradeintel.com (docs: `/tools/`).
No API key, no signup — free daily trial per IP, then $0.001–$0.05/call in
USDC on Base (x402). When the trial is exhausted every integration surfaces
exact pay instructions instead of failing silently.

## Plugins

### 1. ElizaOS — `elizaos-plugin-mekong/`

TypeScript plugin, 5 actions: `MEKONG_WEB_SEARCH`, `MEKONG_BRIEF`,
`MEKONG_AI_VERDICT`, `MEKONG_ENRICH`, `MEKONG_TOKEN_PRICE`.

```bash
npm install @mekong/plugin-x402
# add '@mekong/plugin-x402' to your character's plugins array, then:
elizaos start
```

Status: builds clean (`tsc`), client verified live against `/recommend/`.
Publish: `npm publish --access public` → `@mekong/plugin-x402`.

### 2. Virtuals G.A.M.E. — `virtuals-mekong-plugin/`

Python `game_sdk` Functions for Worker `action_space`: `mekong_web_search`,
`mekong_brief`, `mekong_ai_verdict`, `mekong_enrich`, `mekong_token_price`.

```bash
pip install game_sdk mekong-x402-game
export GAME_API_KEY=<key from https://console.game.virtuals.io/>
python example_worker.py
```

Status: all 5 functions construct + execute live (token price verified:
`ETH: $2253.89`). Publish: `python -m build && twine upload dist/*` →
`mekong-x402-game`; optional PR to `game-by-virtuals/game-python/plugins/`.

## Also existing (reference)

- `langchain-mekong` 0.1.0 on PyPI — LangChain tools for the same fleet
  (`pip install langchain-mekong`), source at
  `~/workspace/x402-agent-demo/python/langchain-mekong/`.
- MCP endpoint: `https://api.mekongtradeintel.com/mcp` (port 4064).

## Payment model (all plugins)

1. Call → free trial quota (per IP, automatic).
2. 402 → exact pay instructions (amount, payTo, asset, network).
3. Sign x402 `exact` USDC transfer on Base → retry with `X-PAYMENT` /
   `PAYMENT-SIGNATURE`. Wallet needs USDC on Base + ~$0.0007 ETH gas.
