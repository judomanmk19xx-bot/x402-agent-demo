# plugin-mekong-x402 — ElizaOS plugin

Pay-per-call API fleet for ElizaOS agents. No API key, no signup — free daily trial, then micropayments in USDC on Base (x402).

## 1-command install

```bash
npm install @mekong/plugin-x402
```

Then add to your character file:

```ts
// src/character.ts
export const character: Character = {
  name: 'Eliza',
  plugins: [
    '@elizaos/plugin-sql',
    '@elizaos/plugin-bootstrap',
    '@mekong/plugin-x402',   // <-- add this
  ],
};
```

Start: `elizaos start` (or `npx elizaos start`). Check the Plugins tab at `http://localhost:3000`.

## Local dev install (this repo)

```bash
cd elizaos-plugin-mekong
npm install
npm run build        # -> dist/
```

Then reference the local path in your character:

```ts
plugins: ['./elizaos-plugin-mekong'],
```

## Actions (5)

| Action | What it does | Price after free trial |
|---|---|---|
| `MEKONG_WEB_SEARCH` | Live web search, deduped + relevance-scored | $0.01/call |
| `MEKONG_BRIEF` | Morning briefing: news + trends + sentiment | $0.05/call |
| `MEKONG_AI_VERDICT` | Token safety verdict SAFE/RISKY/SCAM + reasoning | $0.01/call |
| `MEKONG_ENRICH` | Company enrichment from domain (DNS/WHOIS/SEC) | $0.02/call |
| `MEKONG_TOKEN_PRICE` | Live token price / mcap / liquidity | $0.001/call |

Example prompts: *"Search for Ethereum ETF inflows"*, *"Give me a morning briefing on AI agents"*,
*"Is 0x1234...abcd a honeypot?"*, *"Tell me about stripe.com"*, *"Price of $ETH?"*.

## Payment flow

1. Every call first tries the **free daily trial quota** (per IP, automatic).
2. Trial exhausted → action returns exact pay instructions (`X402PaymentRequired`):
   sign an x402 `exact`-scheme USDC transfer on Base and retry with the
   `X-PAYMENT` (v1) / `PAYMENT-SIGNATURE` (v2) header.
3. Drop-in libraries that handle signing for you: `@x402/fetch`, `x402-axios` (npm).
   Wallet needs USDC on Base + a little ETH for gas (~$0.0007/tx).

## Publish to npm (maintainer)

```bash
npm login
npm publish --access public   # package: @mekong/plugin-x402
```

Registry listing for ElizaOS also wants `images/logo.jpg` (400×400) and
`images/banner.jpg` (1280×640) — add before submitting to the ElizaOS registry.

## Files

- `src/client.ts` — x402 HTTP client (port of the Python `langchain-mekong` client)
- `src/actions/*.ts` — the 5 actions
- `src/plugin.ts` — `Plugin` definition (`plugin-mekong-x402`)
- `src/index.ts` — public exports
