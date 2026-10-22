"""Mekong x402 tools — pay-per-call APIs for AI agents. No signup, no API key.

37 live endpoints on Base (USDC), free daily trial quota on every endpoint.
Paid calls raise a clear error with exact x402 pay instructions once the
trial quota is exhausted — never a silent charge.

Fleet docs: https://api.mekongtradeintel.com/tools/
Verify kit:  https://api.mekongtradeintel.com/tools/verify
"""
from __future__ import annotations

from typing import Any, List, Optional

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel, Field

BASE_URL = "https://api.mekongtradeintel.com"
_TIMEOUT = 60
_FLEET_WALLET = "0x198f3895551B309fF5C5F59e690FB0823d10EA93"
_USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


class MekongPaymentRequired(RuntimeError):
    """HTTP 402 from the fleet: trial exhausted, USDC payment needed."""


def _call(path: str, payload: Optional[dict] = None, timeout: int = _TIMEOUT) -> dict:
    """POST to a fleet endpoint. Returns parsed JSON or raises MekongPaymentRequired."""
    r = requests.post(
        BASE_URL + path,
        json=payload or {},
        headers={"User-Agent": "langchain-community/mekong-x402"},
        timeout=timeout,
    )
    if r.status_code == 402:
        body = r.json() if r.content else {}
        accepts = (body.get("accepts") or [{}])[0]
        amount = accepts.get("amount") or "?"
        try:
            price = f"${int(amount) / 1e6:g}"
        except (TypeError, ValueError):
            price = "?"
        raise MekongPaymentRequired(
            f"x402 payment required for {path} ({price} USDC) — free trial quota exhausted. "
            f"Pay: sign an exact-scheme USDC transfer on Base of {amount} base units "
            f"of {_USDC_BASE} to {_FLEET_WALLET}, base64 the signed x402 payload, "
            f"retry the same request with header 'X-PAYMENT: <payload>'. "
            f"Full guide: https://api.mekongtradeintel.com/tools/verify"
        )
    r.raise_for_status()
    return r.json()


def _lines(items: list, n: int = 10) -> str:
    if not items:
        return "No results."
    return "\n".join(
        f"- {(it.get('title') or it.get('headline') or 'untitled')[:140]}" for it in items[:n]
    )


class WebSearchSchema(BaseModel):
    query: str = Field(description="Search query, e.g. 'Ethereum ETF inflows'")
    num: int = Field(default=5, ge=1, le=10, description="Max results (1-10)")


class MekongWebSearch(BaseTool):
    """Search the live web. Free daily trial, then $0.01/call in USDC on Base (x402). No API key.

    Example usage:
    .. code-block:: python

        tool = MekongWebSearch()
        tool.run({"query": "Ethereum ETF inflows"})
    """

    name: str = "mekong_web_search"
    description: str = (
        "Search the live web and get deduped, relevance-scored results. "
        "No API key needed — free daily trial, then $0.01 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = WebSearchSchema

    def _run(
        self,
        query: str,
        num: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        d = _call("/websearch/", {"query": query, "num": num})
        return _lines(d.get("results") or d.get("items") or [])


class TokenPriceSchema(BaseModel):
    ticker: Optional[str] = Field(
        default=None, description='Token ticker, e.g. "ETH" (may be ambiguous across chains)'
    )
    chain: Optional[str] = Field(default=None, description='Chain, e.g. "base"')
    address: Optional[str] = Field(default=None, description="Token contract address 0x...")


class MekongTokenPrice(BaseTool):
    """Live token price / mcap / liquidity. Free daily trial, then $0.001/call. No API key.

    Example usage:
    .. code-block:: python

        tool = MekongTokenPrice()
        tool.run({"chain": "base", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"})
    """

    name: str = "mekong_token_price"
    description: str = (
        "Live token price, market cap, 24h volume and liquidity via DexScreener. "
        "Use chain+address for exact lookup (ticker alone can be ambiguous across chains). "
        "No API key — free daily trial, then $0.001 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = TokenPriceSchema

    def _run(
        self,
        ticker: Optional[str] = None,
        chain: Optional[str] = None,
        address: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if address:
            body: dict = {"address": address, **({"chain": chain} if chain else {})}
        elif ticker:
            body = {"ticker": ticker}
        else:
            raise ValueError("Provide ticker, or chain+address.")
        d = _call("/tokenprice/", body)
        tok = d.get("token") or {}
        return (
            f"{tok.get('symbol') or d.get('symbol') or '?'}: "
            f"${d.get('priceUsd') or d.get('price') or '?'} | "
            f"mcap ${d.get('marketCap') or '?'} | "
            f"24h vol ${d.get('volume24hUsd') or d.get('volume24h') or '?'}"
        )


class AIVerdictSchema(BaseModel):
    query: str = Field(
        description='Token safety question, e.g. "Is this token a honeypot? 0xabc..."'
    )


class MekongAIVerdict(BaseTool):
    """AI token safety verdict (SAFE/RISKY/SCAM + reasoning). Free trial, then $0.01/call. No API key."""

    name: str = "mekong_ai_verdict"
    description: str = (
        "AI verdict on whether a token is safe: honeypot/tax/owner screening plus "
        "liquidity checks, with written reasoning. Not financial advice. "
        "No API key — free daily trial, then $0.01 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = AIVerdictSchema

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        d = _call("/aiverdict/", {"query": query})
        out = f"Verdict: {d.get('verdict') or d.get('result') or '?'}"
        if d.get("reasoning"):
            out += f"\n{str(d['reasoning'])[:800]}"
        return out


class EnrichSchema(BaseModel):
    domain: str = Field(description='Company domain, e.g. "stripe.com"')


class MekongEnrich(BaseTool):
    """Company enrichment from a domain. Free daily trial, then $0.02/call. No API key."""

    name: str = "mekong_enrich"
    description: str = (
        "Enrich a company from its domain: homepage metadata, DNS, WHOIS, SEC EDGAR. "
        "Public sources only — missing fields come back empty, never hallucinated. "
        "No API key — free daily trial, then $0.02 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = EnrichSchema

    def _run(
        self,
        domain: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        r = requests.get(
            BASE_URL + "/enrich/",
            params={"domain": domain},
            headers={"User-Agent": "langchain-community/mekong-x402"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 402:
            _call("/enrich/", {})  # raises MekongPaymentRequired with details
        r.raise_for_status()
        d = r.json()
        co = d.get("company") or {}
        return (
            f"Company: {co.get('name') or domain}\n"
            f"Description: {str(co.get('description') or '')[:300]}"
        )


class STTSchema(BaseModel):
    audio_url: str = Field(description="Public URL of the audio file to transcribe")
    language: str = Field(default="en", description="Language code, e.g. 'en', 'vi'")


class MekongSTT(BaseTool):
    """Speech-to-text from an audio URL. Free daily trial, then $0.05/call. No API key."""

    name: str = "mekong_stt"
    description: str = (
        "Transcribe audio to text from a public audio URL (99+ languages). "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = STTSchema

    def _run(
        self,
        audio_url: str,
        language: str = "en",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        d = _call("/stt/", {"audio_url": audio_url, "language": language}, timeout=180)
        return str(d.get("text") or d.get("transcript") or "")[:4000]


class BriefSchema(BaseModel):
    topic: str = Field(default="AI agents", description="Briefing topic")
    geo: str = Field(default="US", description="Region code, e.g. 'US', 'VN'")


class MekongBrief(BaseTool):
    """Morning-briefing bundle: news + trends + sentiment, one call. Free trial, then $0.05. No API key."""

    name: str = "mekong_brief"
    description: str = (
        "One-call morning briefing: market news headlines, Google Trends intel and "
        "news sentiment score for a topic/region. "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = BriefSchema

    def _run(
        self,
        topic: str = "AI agents",
        geo: str = "US",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        d = _call("/brief/", {"topic": topic, "geo": geo})
        for key in ("briefing", "brief", "summary", "text"):
            if d.get(key):
                return str(d[key])[:4000]
        return str(d)[:4000]


class TaskRouterSchema(BaseModel):
    task: str = Field(
        description="Describe what you need in plain language, e.g. 'Is this token a honeypot?'"
    )


class MekongTaskRouter(BaseTool):
    """FREE task router — describe a task in plain language, get the right endpoint. Never costs anything."""

    name: str = "mekong_task_router"
    description: str = (
        "FREE — never costs anything, no payment, no key. Describe what you need in "
        "plain language and get the top-3 matching fleet endpoints with prices, paid "
        "URLs and ready curls. Call this first whenever you are unsure which endpoint "
        "fits the task."
    )
    args_schema: type[BaseModel] = TaskRouterSchema

    def _run(
        self,
        task: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        d = _call("/recommend/", {"task": task})
        lines = []
        for r in (d.get("recommendations") or [])[:3]:
            lines.append(
                f"- {r.get('endpoint')} ({r.get('price')}): {r.get('paid_url')}\n"
                f"  try: {r.get('try_curl')}"
            )
        return "\n".join(lines) or "No match — browse https://api.mekongtradeintel.com/tools/"


class MekongX402Toolkit(BaseToolkit):
    """Toolkit bundling all 7 Mekong x402 tools."""

    def get_tools(self) -> List[BaseTool]:
        return [
            MekongTaskRouter(),
            MekongWebSearch(),
            MekongTokenPrice(),
            MekongAIVerdict(),
            MekongEnrich(),
            MekongSTT(),
            MekongBrief(),
        ]


__all__ = [
    "MekongWebSearch",
    "MekongTokenPrice",
    "MekongAIVerdict",
    "MekongEnrich",
    "MekongSTT",
    "MekongBrief",
    "MekongTaskRouter",
    "MekongX402Toolkit",
    "MekongPaymentRequired",
]
