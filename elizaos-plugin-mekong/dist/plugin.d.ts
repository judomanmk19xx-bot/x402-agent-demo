import type { Plugin } from '@elizaos/core';
/**
 * Mekong x402 plugin — pay-per-call API fleet for ElizaOS agents.
 *
 * 5 actions, no API key, no signup:
 *   MEKONG_WEB_SEARCH    live web search ($0.01/call after free trial)
 *   MEKONG_BRIEF         news + trends + sentiment briefing ($0.05/call)
 *   MEKONG_AI_VERDICT    token safety verdict SAFE/RISKY/SCAM ($0.01/call)
 *   MEKONG_ENRICH        company enrichment from domain ($0.02/call)
 *   MEKONG_TOKEN_PRICE   live token price/mcap/liquidity ($0.001/call)
 *
 * Payment model: free daily trial per IP, then x402 micropayments in USDC on
 * Base. When the trial is exhausted each action surfaces exact pay instructions
 * (X402PaymentRequired) instead of failing silently.
 */
export declare const mekongX402Plugin: Plugin;
export default mekongX402Plugin;
