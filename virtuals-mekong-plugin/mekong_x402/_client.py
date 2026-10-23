"""Shared x402 HTTP client for the Mekong pay-per-call fleet (G.A.M.E. plugin).

Protocol:
  1. Call without payment  -> HTTP 402 with JSON body (price, payTo, asset, network)
  2. Sign an exact-scheme USDC transfer on Base, retry with X-PAYMENT header
  3. HTTP 200 with the JSON result

Free daily trial quota per IP applies automatically — no key, no signup.
"""
from __future__ import annotations

import requests

BASE_URL = "https://api.mekongtradeintel.com"
USER_AGENT = "mekong-x402-game/0.1.0 (python)"

FLEET_WALLET = "0x198f3895551B309fF5C5F59e690FB0823d10EA93"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


class X402PaymentRequired(Exception):
    """HTTP 402 — trial exhausted, payment needed. Carries pay instructions."""

    def __init__(self, endpoint: str, price_hint: str, body: dict):
        accepts = (body.get("accepts") or [{}])[0]
        amount_atomic = accepts.get("amount") or accepts.get("maxAmountRequired")
        try:
            amount_usd = f"${int(amount_atomic) / 1e6:g}"
        except (TypeError, ValueError):
            amount_usd = price_hint
        self.endpoint = endpoint
        self.amount_usd = amount_usd
        self.pay_to = accepts.get("payTo", FLEET_WALLET)
        self.asset = accepts.get("asset", USDC_BASE)
        self.network = accepts.get("network", "eip155:8453")
        self.raw_402 = body
        super().__init__(
            f"x402 payment required for {endpoint} ({amount_usd} USDC). "
            f"Free trial quota exhausted. Sign an x402 'exact' USDC transfer on "
            f"Base: {amount_atomic} base units of {self.asset} to {self.pay_to}, "
            f"then retry with X-PAYMENT / PAYMENT-SIGNATURE header. "
            f"Libs: x402-axios / @x402/fetch (npm)."
        )


_PRICE_HINTS = {
    "/websearch": "$0.01",
    "/tokenprice": "$0.001",
    "/aiverdict": "$0.01",
    "/enrich": "$0.02",
    "/brief": "$0.05",
    "/recommend": "free",
}


def x402_call(method: str, path: str, *, json_body=None, params=None, timeout=60) -> dict:
    """Call a fleet endpoint. Returns parsed JSON on 200.

    Raises:
        X402PaymentRequired: on HTTP 402.
        requests.HTTPError: on other HTTP errors.
    """
    url = path if path.startswith("http") else BASE_URL + path
    r = requests.request(
        method.upper(), url, json=json_body, params=params,
        headers={"User-Agent": USER_AGENT}, timeout=timeout,
    )
    if r.status_code == 402:
        try:
            body = r.json()
        except ValueError:
            body = {}
        raise X402PaymentRequired(path, _PRICE_HINTS.get(path.rstrip("/"), "?"), body)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error") and not data.get("results"):
        raise ValueError(f"Fleet error from {path}: {data.get('error')}")
    return data
