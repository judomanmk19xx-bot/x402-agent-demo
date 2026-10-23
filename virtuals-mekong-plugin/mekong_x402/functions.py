"""G.A.M.E. Function definitions for the Mekong x402 pay-per-call fleet.

Each Function wraps one fleet endpoint and is ready to drop into a Worker's
``action_space``. Executables return ``(FunctionResultStatus, feedback, info)``
per the game_sdk contract. x402 402s surface as FAILED with exact pay
instructions in the feedback message (never silent).
"""
from __future__ import annotations

from typing import Tuple

from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus

from ._client import X402PaymentRequired, x402_call


def _ok(feedback: str, info: dict | None = None) -> Tuple[FunctionResultStatus, str, dict]:
    return FunctionResultStatus.DONE, feedback, info or {}


def _fail(msg: str, info: dict | None = None) -> Tuple[FunctionResultStatus, str, dict]:
    return FunctionResultStatus.FAILED, msg, info or {}


# ------------------------------------------------------------------ formatters
def _fmt_search(d: dict) -> str:
    items = d.get("results") or d.get("items") or []
    if not items:
        return "No results."
    return "\n".join(
        f"- {str(it.get('title') or it.get('headline') or 'untitled')[:140]}"
        for it in items[:10]
    )


def _fmt_brief(d: dict) -> str:
    for key in ("briefing", "brief", "summary", "text"):
        if d.get(key):
            return str(d[key])[:4000]
    return str(d)[:4000]


def _fmt_verdict(d: dict) -> str:
    verdict = d.get("verdict") or d.get("result") or "?"
    score = d.get("risk_score", d.get("score"))
    reasoning = d.get("reasoning") or d.get("summary") or ""
    out = f"Verdict: {verdict}"
    if score is not None:
        out += f" (risk score {score})"
    if reasoning:
        out += f"\n{str(reasoning)[:800]}"
    return out


def _fmt_enrich(d: dict) -> str:
    co = d.get("company") or {}
    web = d.get("web") or {}
    dns = d.get("dns") or {}
    lines = [
        f"Company: {co.get('name') or d.get('domain') or '?'}",
        f"Website: {co.get('website') or web.get('url') or '?'}",
        f"Description: {str(co.get('description') or '')[:300]}",
    ]
    if dns.get("a"):
        lines.append(f"DNS A: {', '.join(map(str, dns['a'][:3]))}")
    if d.get("partial"):
        lines.append("(partial data — some sources unreachable)")
    return "\n".join(lines)


def _fmt_price(d: dict) -> str:
    tok = d.get("token") or {}
    return (
        f"{tok.get('symbol') or d.get('symbol') or '?'}: "
        f"${d.get('priceUsd') or d.get('price') or '?'} | "
        f"mcap ${d.get('marketCap') or '?'} | "
        f"24h vol ${d.get('volume24hUsd') or d.get('volume24h') or '?'}"
    )


# ------------------------------------------------------------------ executables
def _web_search(query: str, num: int = 5, **_) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        return _ok(_fmt_search(x402_call("POST", "/websearch/", json_body={"query": query, "num": num})))
    except X402PaymentRequired as e:
        return _fail(f"Trial exhausted. Pay to continue: {e}", {"pay_to": e.pay_to, "amount": e.amount_usd})
    except Exception as e:  # noqa: BLE001
        return _fail(f"Web search failed: {e}")


def _brief(topic: str = "AI agents", geo: str = "US", **_) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        return _ok(_fmt_brief(x402_call("POST", "/brief/", json_body={"topic": topic, "geo": geo})))
    except X402PaymentRequired as e:
        return _fail(f"Trial exhausted. Pay to continue: {e}", {"pay_to": e.pay_to, "amount": e.amount_usd})
    except Exception as e:  # noqa: BLE001
        return _fail(f"Briefing failed: {e}")


def _ai_verdict(query: str, **_) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        return _ok(_fmt_verdict(x402_call("POST", "/aiverdict/", json_body={"query": query})))
    except X402PaymentRequired as e:
        return _fail(f"Trial exhausted. Pay to continue: {e}", {"pay_to": e.pay_to, "amount": e.amount_usd})
    except Exception as e:  # noqa: BLE001
        return _fail(f"Verdict failed: {e}")


def _enrich(domain: str, **_) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        return _ok(_fmt_enrich(x402_call("GET", "/enrich/", params={"domain": domain})))
    except X402PaymentRequired as e:
        return _fail(f"Trial exhausted. Pay to continue: {e}", {"pay_to": e.pay_to, "amount": e.amount_usd})
    except Exception as e:  # noqa: BLE001
        return _fail(f"Enrichment failed: {e}")


def _token_price(ticker: str = "", address: str = "", chain: str = "", **_) -> Tuple[FunctionResultStatus, str, dict]:
    try:
        body: dict = {"address": address, "chain": chain} if address else {"ticker": ticker}
        if not (address or ticker):
            return _fail("Provide ticker (e.g. ETH) or contract address.")
        return _ok(_fmt_price(x402_call("POST", "/tokenprice/", json_body=body)))
    except X402PaymentRequired as e:
        return _fail(f"Trial exhausted. Pay to continue: {e}", {"pay_to": e.pay_to, "amount": e.amount_usd})
    except Exception as e:  # noqa: BLE001
        return _fail(f"Price lookup failed: {e}")


# ------------------------------------------------------------------ Functions
MEKONG_FUNCTIONS: list[Function] = [
    Function(
        fn_name="mekong_web_search",
        fn_description=(
            "Search the live web and get deduped, relevance-scored results. "
            "Free daily trial, then $0.01/call in USDC on Base via x402. "
            "Use for current information, news, anything beyond training data."
        ),
        args=[
            Argument(name="query", description="Search query, e.g. 'Ethereum ETF inflows'", type="string"),
            Argument(name="num", description="Max results 1-10", type="integer", optional=True),
        ],
        hint="mekong_web_search(query='Ethereum ETF inflows', num=5)",
        executable=_web_search,
    ),
    Function(
        fn_name="mekong_brief",
        fn_description=(
            "One-call morning briefing: market news headlines, Google Trends intel and "
            "news sentiment score for a topic/region. Free daily trial, then $0.05/call "
            "in USDC on Base via x402."
        ),
        args=[
            Argument(name="topic", description="Briefing topic, e.g. 'AI agents'", type="string", optional=True),
            Argument(name="geo", description="Region code, e.g. 'US', 'VN'", type="string", optional=True),
        ],
        hint="mekong_brief(topic='AI agents', geo='US')",
        executable=_brief,
    ),
    Function(
        fn_name="mekong_ai_verdict",
        fn_description=(
            "AI verdict on whether a crypto token is safe: honeypot/tax/owner screening "
            "plus liquidity checks, with written reasoning. Not financial advice. "
            "Free daily trial, then $0.01/call in USDC on Base via x402."
        ),
        args=[
            Argument(name="query", description="Token safety question, e.g. 'Is 0xabc... a honeypot?'", type="string"),
        ],
        hint="mekong_ai_verdict(query='Is 0xabc... a honeypot?')",
        executable=_ai_verdict,
    ),
    Function(
        fn_name="mekong_enrich",
        fn_description=(
            "Enrich a company from its domain: homepage metadata, DNS, WHOIS, SEC EDGAR. "
            "Public sources only. Free daily trial, then $0.02/call in USDC on Base via x402."
        ),
        args=[
            Argument(name="domain", description="Company domain, e.g. 'stripe.com'", type="string"),
        ],
        hint="mekong_enrich(domain='stripe.com')",
        executable=_enrich,
    ),
    Function(
        fn_name="mekong_token_price",
        fn_description=(
            "Live token price, market cap, 24h volume and liquidity. "
            "Free daily trial, then $0.001/call in USDC on Base via x402."
        ),
        args=[
            Argument(name="ticker", description="Token ticker, e.g. 'ETH'", type="string", optional=True),
            Argument(name="address", description="Contract address 0x... (exact, preferred)", type="string", optional=True),
            Argument(name="chain", description="Chain for address lookup, e.g. 'base'", type="string", optional=True),
        ],
        hint="mekong_token_price(ticker='ETH')",
        executable=_token_price,
    ),
]
