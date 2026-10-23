/**
 * Shared x402 HTTP client for the Mekong pay-per-call fleet.
 *
 * Protocol (identical to the Python langchain-mekong client):
 *   1. Call without payment  -> HTTP 402 with JSON body (price, payTo, asset, network)
 *   2. Sign an exact-scheme USDC transfer on Base, retry with X-PAYMENT header
 *   3. HTTP 200 with the JSON result
 *
 * Free daily trial quota per IP applies automatically — no key, no signup.
 * When the trial is exhausted the call throws X402PaymentRequired carrying
 * everything needed to pay (or to hand to an x402 client lib like @x402/fetch).
 */

export const BASE_URL = 'https://api.mekongtradeintel.com';
export const USER_AGENT = 'mekong-x402-elizaos/0.1.0';
export const FLEET_WALLET = '0x198f3895551B309fF5C5F59e690FB0823d10EA93';
export const USDC_BASE = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';

export interface AcceptsEntry {
  scheme?: string;
  network?: string;
  amount?: string;
  maxAmountRequired?: string;
  asset?: string;
  payTo?: string;
  maxTimeoutSeconds?: number;
}

export class X402PaymentRequired extends Error {
  endpoint: string;
  amountUsd: string;
  payTo: string;
  asset: string;
  network: string;
  raw402: Record<string, unknown>;

  constructor(endpoint: string, priceHint: string, body: Record<string, unknown>) {
    const accepts = ((body.accepts as AcceptsEntry[]) || [{}])[0] || {};
    const amountAtomic = accepts.amount || accepts.maxAmountRequired;
    let amountUsd = priceHint;
    try {
      amountUsd = `$${Number(amountAtomic) / 1e6}`;
    } catch {
      /* keep hint */
    }
    super(
      `x402 payment required for ${endpoint} (${amountUsd} USDC).\n` +
        `Free trial quota for your IP is exhausted.\n` +
        `To pay:\n` +
        `  1. Sign an x402 'exact'-scheme USDC transfer on Base (eip155:8453): ` +
        `${amountAtomic} base units of ${accepts.asset || USDC_BASE} ` +
        `to ${accepts.payTo || FLEET_WALLET}.\n` +
        `  2. Base64-encode the signed x402 payload.\n` +
        `  3. Retry the SAME request with header 'X-PAYMENT: <base64>' (v1) ` +
        `or 'PAYMENT-SIGNATURE' (v2).\n` +
        `Libraries that do steps 2-3 for you: @x402/fetch, x402-axios (npm). ` +
        `Wallet needs USDC on Base + a little ETH for gas (~$0.0007/tx).`
    );
    this.name = 'X402PaymentRequired';
    this.endpoint = endpoint;
    this.amountUsd = amountUsd;
    this.payTo = accepts.payTo || FLEET_WALLET;
    this.asset = accepts.asset || USDC_BASE;
    this.network = accepts.network || 'eip155:8453';
    this.raw402 = body;
  }
}

const PRICE_HINTS: Record<string, string> = {
  '/websearch': '$0.01',
  '/tokenprice': '$0.001',
  '/aiverdict': '$0.01',
  '/enrich': '$0.02',
  '/brief': '$0.05',
  '/recommend': 'free',
};

export interface CallOptions {
  jsonBody?: Record<string, unknown>;
  params?: Record<string, string>;
  timeoutMs?: number;
}

/** Call a fleet endpoint. Returns parsed JSON on 200. Throws X402PaymentRequired on 402. */
export async function x402Call(
  method: 'GET' | 'POST',
  path: string,
  opts: CallOptions = {}
): Promise<Record<string, unknown>> {
  const url = new URL(path.startsWith('http') ? path : BASE_URL + path);
  if (opts.params) {
    for (const [k, v] of Object.entries(opts.params)) url.searchParams.set(k, v);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), opts.timeoutMs || 60000);
  try {
    const res = await fetch(url.toString(), {
      method,
      headers: {
        'User-Agent': USER_AGENT,
        ...(opts.jsonBody ? { 'Content-Type': 'application/json' } : {}),
      },
      body: opts.jsonBody ? JSON.stringify(opts.jsonBody) : undefined,
      signal: controller.signal,
    });
    if (res.status === 402) {
      let body: Record<string, unknown> = {};
      try {
        body = (await res.json()) as Record<string, unknown>;
      } catch {
        /* non-JSON 402 */
      }
      throw new X402PaymentRequired(
        path,
        PRICE_HINTS[path.replace(/\/$/, '')] || '?',
        body
      );
    }
    if (!res.ok) {
      throw new Error(`Fleet HTTP ${res.status} from ${path}: ${(await res.text()).slice(0, 300)}`);
    }
    const data = (await res.json()) as Record<string, unknown>;
    if (data.error && !data.results) {
      throw new Error(`Fleet error from ${path}: ${data.error}`);
    }
    return data;
  } finally {
    clearTimeout(timer);
  }
}
