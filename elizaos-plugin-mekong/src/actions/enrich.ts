import type { Action } from '@elizaos/core';
import { x402Call, X402PaymentRequired } from '../client.js';

function fmtEnrich(d: Record<string, unknown>): string {
  const co = (d.company as Record<string, unknown>) || {};
  const web = (d.web as Record<string, unknown>) || {};
  const dns = (d.dns as Record<string, unknown>) || {};
  const lines = [
    `Company: ${co.name || d.domain || '?'}`,
    `Website: ${co.website || web.url || '?'}`,
    `Description: ${String(co.description || '').slice(0, 300)}`,
  ];
  const a = dns.a as string[] | undefined;
  if (a?.length) lines.push(`DNS A: ${a.slice(0, 3).join(', ')}`);
  if (d.partial) lines.push('(partial data — some sources unreachable)');
  return lines.join('\n');
}

/** Company enrichment from a domain. Free trial, then $0.02/call. */
export const enrichAction: Action = {
  name: 'MEKONG_ENRICH',
  similes: ['ENRICH_COMPANY', 'COMPANY_LOOKUP', 'MEKONG_COMPANY'],
  description:
    'Enrich a company from its domain via the Mekong x402 fleet: homepage metadata, ' +
    'DNS, WHOIS, SEC EDGAR. Public sources only — missing fields come back empty, ' +
    'never hallucinated. No API key — free daily trial, then $0.02 per call in USDC on Base. ' +
    'Use when the user asks about a company behind a domain.',
  validate: async () => true,
  handler: async (runtime, message, state, options, callback) => {
    try {
      const text = (message.content.text || '').trim();
      const m = text.match(/([a-z0-9-]+\.)+[a-z]{2,}/i);
      if (!m) throw new Error('No domain found in the message.');
      const data = await x402Call('GET', '/enrich/', { params: { domain: m[0] } });
      const out = fmtEnrich(data);
      if (callback) await callback({ text: out });
      return { text: out, success: true };
    } catch (e) {
      const msg =
        e instanceof X402PaymentRequired
          ? `Enrichment trial exhausted. ${e.message}`
          : `Enrichment failed: ${(e as Error).message}`;
      if (callback) await callback({ text: msg, error: true });
      return { text: msg, success: false, error: e as Error };
    }
  },
  examples: [
    [
      { user: 'user', content: { text: 'Tell me about stripe.com' } },
      {
        user: 'assistant',
        content: { text: 'I will look up that company.', action: 'MEKONG_ENRICH' },
      },
    ],
  ],
};
