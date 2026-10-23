import type { Plugin } from '@elizaos/core';
import { webSearchAction } from './actions/websearch.js';
import { briefAction } from './actions/brief.js';
import { aiVerdictAction } from './actions/aiverdict.js';
import { enrichAction } from './actions/enrich.js';
import { tokenPriceAction } from './actions/tokenprice.js';

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
export const mekongX402Plugin: Plugin = {
  name: 'plugin-mekong-x402',
  description:
    'Mekong x402 pay-per-call API fleet: live web search, AI morning briefings, ' +
    'token safety verdicts, company enrichment and token prices. Free daily trial, ' +
    'then micropayments in USDC on Base — no API key, no signup.',
  actions: [webSearchAction, briefAction, aiVerdictAction, enrichAction, tokenPriceAction],
  evaluators: [],
  providers: [],

  init: async (_config, runtime) => {
    runtime.logger?.info?.('Mekong x402 plugin loaded — 5 actions registered');
  },
};

export default mekongX402Plugin;
