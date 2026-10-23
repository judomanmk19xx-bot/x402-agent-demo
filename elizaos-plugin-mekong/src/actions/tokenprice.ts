import type { Action } from '@elizaos/core';
import { x402Call, X402PaymentRequired } from '../client.js';

function fmtPrice(d: Record<string, unknown>): string {
  const tok = (d.token as Record<string, unknown>) || {};
  const sym = tok.symbol || d.symbol || '?';
  const price = d.priceUsd || d.price || '?';
  const mcap = d.marketCap || '?';
  const vol = d.volume24hUsd || d.volume24h || '?';
  return `${sym}: $${price} | mcap $${mcap} | 24h vol $${vol}`;
}

/** Token price / market cap / liquidity. Free trial, then $0.001/call. */
export const tokenPriceAction: Action = {
  name: 'MEKONG_TOKEN_PRICE',
  similes: ['TOKEN_PRICE', 'GET_PRICE', 'MEKONG_PRICE'],
  description:
    'Live token price, market cap, 24h volume and liquidity via the Mekong x402 fleet. ' +
    'Use chain+address for exact lookup (ticker alone can be ambiguous across chains). ' +
    'No API key — free daily trial, then $0.001 per call in USDC on Base. ' +
    'Use when the user asks for a token price.',
  validate: async () => true,
  handler: async (runtime, message, state, options, callback) => {
    try {
      const text = (message.content.text || '').trim();
      const addrMatch = text.match(/0x[a-fA-F0-9]{40}/);
      let body: Record<string, unknown>;
      if (addrMatch) {
        const chainMatch = text.match(/\b(base|ethereum|solana|bsc|arbitrum)\b/i);
        body = { address: addrMatch[0] };
        if (chainMatch) body.chain = chainMatch[1].toLowerCase();
      } else {
        const tickerMatch = text.match(/\$([A-Za-z]{2,10})/) || text.match(/\b([A-Z]{2,10})\b/);
        if (!tickerMatch) throw new Error('No ticker ($XYZ) or contract address found.');
        body = { ticker: tickerMatch[1].toUpperCase() };
      }
      const data = await x402Call('POST', '/tokenprice/', { jsonBody: body });
      const out = fmtPrice(data);
      if (callback) await callback({ text: out });
      return { text: out, success: true };
    } catch (e) {
      const msg =
        e instanceof X402PaymentRequired
          ? `Price trial exhausted. ${e.message}`
          : `Price lookup failed: ${(e as Error).message}`;
      if (callback) await callback({ text: msg, error: true });
      return { text: msg, success: false, error: e as Error };
    }
  },
  examples: [
    [
      { user: 'user', content: { text: 'What is the price of $ETH?' } },
      {
        user: 'assistant',
        content: { text: 'I will check the price.', action: 'MEKONG_TOKEN_PRICE' },
      },
    ],
  ],
};
