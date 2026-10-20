#!/usr/bin/env node
/**
 * x402-agent-demo — Token due-diligence agent (Node.js)
 *
 * Pipeline: tokenprice ($0.001) -> aiverdict ($0.01) -> websearch ($0.01)
 * Total: ~$0.021 per run.
 *
 * Modes:
 *   node agent.mjs                      free trial, no wallet, no signup
 *   PRIVATE_KEY=0x... node agent.mjs    paid x402 flow (USDC on Base)
 *
 * NOTE: use the /api/ URL form (e.g. /tokenprice/api/token-price). The short
 * form (/tokenprice/) currently skips the free trial due to a trailing-slash
 * quirk in trial routing — the /api/ form always works.
 */
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const BASE = "https://api.mekongtradeintel.com";
const UA = { "Content-Type": "application/json", "User-Agent": "x402-agent-demo/1.0" };

// A real token on Base: USDC (safe, always resolves)
const TOKEN = {
  chain: "base",
  contract: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  name: "USDC",
};

const COSTS = { tokenprice: 0.001, aiverdict: 0.01, websearch: 0.01 };

function getFetcher() {
  const pk = process.env.PRIVATE_KEY;
  if (pk && pk.startsWith("0x")) {
    const account = privateKeyToAccount(pk);
    console.log(`[paid] payer wallet: ${account.address}`);
    const client = new x402Client()
      .register("eip155:*", new ExactEvmScheme(account))
      .setSpendControls({ maxAmountPerPayment: "$1" });
    return { f: wrapFetchWithPayment(fetch, client), mode: "paid" };
  }
  console.log("[free] trial mode — no wallet, no signup");
  return { f: fetch, mode: "free-trial" };
}

async function call(f, path, body, label, price) {
  const t0 = Date.now();
  const res = await f(`${BASE}${path}`, {
    method: "POST",
    headers: UA,
    body: JSON.stringify(body),
  });
  const ms = Date.now() - t0;
  const data = await res.json().catch(() => ({}));
  const trialLeft = res.headers.get("x-free-remaining");
  console.log(
    `\n== ${label} ==\nHTTP ${res.status} in ${ms}ms | price $${price}/call` +
      (trialLeft !== null ? ` | trial left: ${trialLeft}` : "")
  );
  if (res.status === 402) {
    console.error("Got 402 — free trial exhausted. Set PRIVATE_KEY for paid mode.");
    process.exit(2);
  }
  if (res.status !== 200) {
    console.error("Unexpected status:", JSON.stringify(data).slice(0, 300));
    process.exit(1);
  }
  return data;
}

const { f, mode } = getFetcher();
let spent = 0;

console.log(`\nToken due-diligence agent — target: ${TOKEN.name} (${TOKEN.contract}) [${mode}]`);

// 1) Price + market data
const px = await call(f, "/tokenprice/api/token-price", { chain: TOKEN.chain, address: TOKEN.contract }, "1/3 tokenprice — live market data", COSTS.tokenprice);
spent += COSTS.tokenprice;
console.log(`price: $${px.priceUsd} | mcap: $${px.marketCap} | 24h vol: $${px.volume24hUsd} | liquidity: $${px.liquidityUsd}`);

// 2) AI security verdict on the contract
const vd = await call(f, "/aiverdict/api/verdict", { chain: TOKEN.chain, contract: TOKEN.contract }, "2/3 aiverdict — contract security verdict", COSTS.aiverdict);
spent += COSTS.aiverdict;
console.log(`verdict: ${vd.verdict} (risk ${vd.risk_score}/100, confidence ${vd.confidence}%) | flags: ${(vd.flags || []).join(", ") || "none"}`);
console.log(`summary: ${(vd.summary || "").slice(0, 160)}...`);

// 3) Latest news
const nw = await call(f, "/websearch/api/websearch", { query: `${TOKEN.name} token news`, num: 5 }, "3/3 websearch — latest headlines", COSTS.websearch);
spent += COSTS.websearch;
const items = nw.results || nw.items || [];
items.slice(0, 3).forEach((it, i) => console.log(`  ${i + 1}. ${(it.title || it.headline || "").slice(0, 90)}`));

console.log(`\nDone. Total data cost this run: $${spent.toFixed(3)} (${mode}).`);
console.log("Docs: https://api.mekongtradeintel.com/tools/ | Pricing: https://api.mekongtradeintel.com/pricing");
