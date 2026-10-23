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
export declare const BASE_URL = "https://api.mekongtradeintel.com";
export declare const USER_AGENT = "mekong-x402-elizaos/0.1.0";
export declare const FLEET_WALLET = "0x198f3895551B309fF5C5F59e690FB0823d10EA93";
export declare const USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";
export interface AcceptsEntry {
    scheme?: string;
    network?: string;
    amount?: string;
    maxAmountRequired?: string;
    asset?: string;
    payTo?: string;
    maxTimeoutSeconds?: number;
}
export declare class X402PaymentRequired extends Error {
    endpoint: string;
    amountUsd: string;
    payTo: string;
    asset: string;
    network: string;
    raw402: Record<string, unknown>;
    constructor(endpoint: string, priceHint: string, body: Record<string, unknown>);
}
export interface CallOptions {
    jsonBody?: Record<string, unknown>;
    params?: Record<string, string>;
    timeoutMs?: number;
}
/** Call a fleet endpoint. Returns parsed JSON on 200. Throws X402PaymentRequired on 402. */
export declare function x402Call(method: 'GET' | 'POST', path: string, opts?: CallOptions): Promise<Record<string, unknown>>;
