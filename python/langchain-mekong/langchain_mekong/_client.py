"""Shared HTTP client for the Mekong x402 pay-per-call fleet.

Every endpoint speaks the same protocol:
  1. Call without payment  -> HTTP 402 with a JSON body (price, payTo, asset, network)
  2. Sign an exact-scheme USDC transfer on Base and retry with the X-PAYMENT header
  3. HTTP 200 with the JSON result

Free daily trial quota per IP applies automatically — no key, no signup.
"""
from __future__ import annotations

import requests

BASE_URL = "https://api.mekongtradeintel.com"
USER_AGENT = "mekong-x402/0.1.0 (python)"

#: Fleet agent wallet (receives USDC on Base). Never send anything else here.
FLEET_WALLET = "0x198f3895551B309fF5C5F59e690FB0823d10EA93"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


class X402PaymentRequired(Exception):
    """Raised when the fleet answers HTTP 402 (trial exhausted / no payment).

    Carries everything an operator needs to pay by hand or wire up an x402
    client (e.g. x402-axios / x402-fetch in JS, or any EIP-712 signer):
    price, payTo, asset, network, and the exact steps.
    """

    def __init__(self, endpoint: str, price_usd: str, body: dict):
        accepts = (body.get("accepts") or [{}])[0]
        amount_atomic = accepts.get("amount") or accepts.get("maxAmountRequired")
        try:
            amount_usd = f"${int(amount_atomic) / 1e6:g}"
        except (TypeError, ValueError):
            amount_usd = price_usd
        self.endpoint = endpoint
        self.amount_usd = amount_usd
        self.pay_to = accepts.get("payTo", FLEET_WALLET)
        self.asset = accepts.get("asset", USDC_BASE)
        self.network = accepts.get("network", "eip155:8453")
        self.raw_402 = body
        super().__init__(
            f"x402 payment required for {endpoint} ({amount_usd} USDC).\n"
            f"Free trial quota for your IP is exhausted.\n"
            f"To pay:\n"
            f"  1. Sign an x402 'exact'-scheme USDC transfer on Base "
            f"(eip155:8453): {amount_atomic} base units of {self.asset} "
            f"to {self.pay_to}.\n"
            f"  2. Base64-encode the signed x402 payload.\n"
            f"  3. Retry the SAME request with header "
            f"'X-PAYMENT: <base64-payload>' (v1) or 'PAYMENT-SIGNATURE' (v2).\n"
            f"Libraries that do 2-3 for you: x402-axios / x402-fetch (npm). "
            f"Your wallet needs USDC on Base + a little ETH for gas (~$0.0007/tx).\n"
            f"Full one-command verify kit: "
            f"https://api.mekongtradeintel.com/tools/verify"
        )


def x402_call(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
    files: dict | None = None,
    timeout: int = 60,
) -> dict:
    """Call a fleet endpoint. Returns parsed JSON on 200.

    Raises:
        X402PaymentRequired: on HTTP 402 (trial exhausted, payment needed).
        requests.HTTPError: on other HTTP errors.
    """
    url = path if path.startswith("http") else BASE_URL + path
    r = requests.request(
        method.upper(),
        url,
        json=json_body,
        params=params,
        files=files,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    if r.status_code == 402:
        try:
            body = r.json()
        except ValueError:
            body = {}
        # price hint from the path table below; the 402 body is authoritative
        raise X402PaymentRequired(path, _PRICE_HINTS.get(path.rstrip("/"), "?"), body)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and data.get("error") and not data.get("results"):
        # some endpoints return 200 with an error payload on bad input
        raise ValueError(f"Fleet error from {path}: {data.get('error')}")
    return data


# Advertised per-call prices (the 402 body is authoritative at call time).
_PRICE_HINTS = {
    "/websearch": "$0.01",
    "/tokenprice": "$0.001",
    "/aiverdict": "$0.01",
    "/enrich": "$0.02",
    "/stt": "$0.05",
    "/brief": "$0.05",
    "/recommend": "free",
}
