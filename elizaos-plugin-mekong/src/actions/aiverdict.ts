import type { Action } from '@elizaos/core';
import { x402Call, X402PaymentRequired } from '../client.js';

function fmtVerdict(d: Record<string, unknown>): string {
  const verdict = d.verdict || d.result || '?';
  const score = d.risk_score ?? d.score;
  const reasoning = d.reasoning || d.summary || '';
  let out = `Verdict: ${verdict}`;
  if (score !== undefined && score !== null) out += ` (risk score ${score})`;
  if (reasoning) out += `\n${String(reasoning).slice(0, 800)}`;
  return out;
}

/** AI token safety verdict (SAFE/RISKY/SCAM + reasoning). Free trial, then $0.01/call. */
export const aiVerdictAction: Action = {
  name: 'MEKONG_AI_VERDICT',
  similes: ['TOKEN_VERDICT', 'CHECK_TOKEN_SAFETY', 'MEKONG_VERDICT'],
  description:
    'AI verdict on whether a crypto token is safe (honeypot/tax/owner screening plus ' +
    'liquidity checks) with written reasoning, via the Mekong x402 fleet. Not financial advice. ' +
    'No API key — free daily trial, then $0.01 per call in USDC on Base. ' +
    'Use when the user asks if a token is safe, a scam, or a honeypot.',
  validate: async () => true,
  handler: async (runtime, message, state, options, callback) => {
    try {
      const query = (message.content.text || '').trim();
      if (!query) throw new Error('No token question provided.');
      const data = await x402Call('POST', '/aiverdict/', { jsonBody: { query } });
      const out = fmtVerdict(data);
      if (callback) await callback({ text: out });
      return { text: out, success: true };
    } catch (e) {
      const msg =
        e instanceof X402PaymentRequired
          ? `Verdict trial exhausted. ${e.message}`
          : `Verdict failed: ${(e as Error).message}`;
      if (callback) await callback({ text: msg, error: true });
      return { text: msg, success: false, error: e as Error };
    }
  },
  examples: [
    [
      { user: 'user', content: { text: 'Is 0x1234...abcd a honeypot?' } },
      {
        user: 'assistant',
        content: { text: 'I will check that token for you.', action: 'MEKONG_AI_VERDICT' },
      },
    ],
  ],
};
