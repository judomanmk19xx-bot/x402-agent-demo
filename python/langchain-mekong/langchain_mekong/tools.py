"""LangChain-native tools for the Mekong x402 fleet.

    from langchain_mekong.tools import WebSearchTool, TaskRouterTool

    tools = [WebSearchTool(), TaskRouterTool()]
    # plug into any LangChain agent; paid calls raise X402PaymentRequired
    # with exact pay instructions once the free trial quota is exhausted.

Requires ``pip install mekong-x402[langchain]`` for production use;
imports cleanly without langchain-core (shim) for inspection/testing.
"""
from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel, Field

from ._client import x402_call
from ._compat import LangChainBaseTool


# ---------------------------------------------------------------- args schemas
class WebSearchArgs(BaseModel):
    query: str = Field(description="Search query, e.g. 'Ethereum ETF inflows'")
    num: int = Field(default=5, ge=1, le=10, description="Max results (1-10)")


class TokenPriceArgs(BaseModel):
    ticker: Optional[str] = Field(
        default=None, description='Token ticker, e.g. "ETH" (may be ambiguous across chains)'
    )
    chain: Optional[str] = Field(
        default=None, description='Chain for exact lookup, e.g. "base" (use with address)'
    )
    address: Optional[str] = Field(
        default=None, description="Token contract address 0x... (use with chain; exact, preferred)"
    )


class AIVerdictArgs(BaseModel):
    query: str = Field(
        description='Token safety question, e.g. "Is this token a honeypot? 0xabc..."'
    )


class EnrichArgs(BaseModel):
    domain: str = Field(description='Company domain, e.g. "stripe.com"')


class STTArgs(BaseModel):
    audio_url: str = Field(description="Public URL of the audio file to transcribe")
    language: str = Field(default="en", description="Language code, e.g. 'en', 'vi'")


class BriefArgs(BaseModel):
    topic: str = Field(default="AI agents", description="Briefing topic")
    geo: str = Field(default="US", description="Region code, e.g. 'US', 'VN'")


class TaskRouterArgs(BaseModel):
    task: str = Field(
        description="Describe what you need in plain language, e.g. 'Is this token a honeypot?'"
    )


# ---------------------------------------------------------------- formatters
def _fmt_search(d: dict) -> str:
    items = d.get("results") or d.get("items") or []
    if not items:
        return "No results."
    return "\n".join(
        f"- {(it.get('title') or it.get('headline') or 'untitled')[:140]}"
        for it in items[:10]
    )


def _fmt_tokenprice(d: dict) -> str:
    tok = d.get("token") or {}
    sym = tok.get("symbol") or d.get("symbol") or "?"
    price = d.get("priceUsd") or d.get("price") or "?"
    mcap = d.get("marketCap") or "?"
    vol = d.get("volume24hUsd") or d.get("volume24h") or "?"
    return f"{sym}: ${price} | mcap ${mcap} | 24h vol ${vol}"


def _fmt_aiverdict(d: dict) -> str:
    verdict = d.get("verdict") or d.get("result") or "?"
    reasoning = d.get("reasoning") or d.get("summary") or ""
    score = d.get("risk_score") or d.get("score")
    out = f"Verdict: {verdict}"
    if score is not None:
        out += f" (risk score {score})"
    if reasoning:
        out += f"\n{str(reasoning)[:800]}"
    return out


def _fmt_enrich(d: dict) -> str:
    co = d.get("company") or {}
    lines = [
        f"Company: {co.get('name') or d.get('domain') or '?'}",
        f"Website: {co.get('website') or (d.get('web') or {}).get('url') or '?'}",
        f"Description: {str(co.get('description') or '')[:300]}",
    ]
    dns = d.get("dns") or {}
    if dns.get("a"):
        lines.append(f"DNS A: {', '.join(map(str, dns['a'][:3]))}")
    if d.get("partial"):
        lines.append("(partial data — some sources unreachable)")
    return "\n".join(lines)


def _fmt_stt(d: dict) -> str:
    text = d.get("text") or d.get("transcript") or ""
    lang = d.get("language") or "?"
    conf = d.get("confidence")
    out = f"[{lang}" + (f" conf={conf}]" if conf is not None else "]")
    return out + "\n" + str(text)[:4000]


def _fmt_brief(d: dict) -> str:
    for key in ("briefing", "brief", "summary", "text"):
        if d.get(key):
            return str(d[key])[:4000]
    return str(d)[:4000]


def _fmt_recommend(d: dict) -> str:
    recs = d.get("recommendations") or []
    if not recs:
        return "No matching endpoint found. Browse https://api.mekongtradeintel.com/tools/"
    lines = []
    for r in recs[:3]:
        lines.append(
            f"- {r.get('endpoint')} ({r.get('price')}): {r.get('paid_url')}\n"
            f"  why: {r.get('why')}\n"
            f"  try: {r.get('try_curl')}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- tools
class WebSearchTool(LangChainBaseTool):
    """Live web search. Free trial daily, then $0.01/call USDC on Base (x402)."""

    name: str = "mekong_web_search"
    description: str = (
        "Search the live web and get deduped, relevance-scored results. "
        "No API key needed — free daily trial, then $0.01 per call in USDC on Base via x402. "
        "Raises X402PaymentRequired with exact pay instructions when the trial is exhausted."
    )
    args_schema: Type[BaseModel] = WebSearchArgs

    def _run(self, query: str, num: int = 5) -> str:
        return _fmt_search(x402_call("POST", "/websearch/", json_body={"query": query, "num": num}))


class TokenPriceTool(LangChainBaseTool):
    """Token price / market cap / liquidity via DexScreener. Free trial, then $0.001/call."""

    name: str = "mekong_token_price"
    description: str = (
        "Live token price, market cap, 24h volume and liquidity. "
        "Use chain+address for exact lookup (ticker alone can be ambiguous across chains). "
        "No API key — free daily trial, then $0.001 per call in USDC on Base via x402."
    )
    args_schema: Type[BaseModel] = TokenPriceArgs

    def _run(
        self,
        ticker: Optional[str] = None,
        chain: Optional[str] = None,
        address: Optional[str] = None,
    ) -> str:
        body: dict = {}
        if address:
            body = {"address": address, **({"chain": chain} if chain else {})}
        elif ticker:
            body = {"ticker": ticker}
        else:
            raise ValueError("Provide ticker, or chain+address.")
        return _fmt_tokenprice(x402_call("POST", "/tokenprice/", json_body=body))


class AIVerdictTool(LangChainBaseTool):
    """AI token safety verdict (SAFE/RISKY/SCAM + reasoning). Free trial, then $0.01/call."""

    name: str = "mekong_ai_verdict"
    description: str = (
        "AI verdict on whether a token is safe: honeypot/tax/owner screening plus "
        "liquidity checks, with written reasoning. Not financial advice. "
        "No API key — free daily trial, then $0.01 per call in USDC on Base via x402."
    )
    args_schema: Type[BaseModel] = AIVerdictArgs

    def _run(self, query: str) -> str:
        return _fmt_aiverdict(x402_call("POST", "/aiverdict/", json_body={"query": query}))


class EnrichTool(LangChainBaseTool):
    """Company enrichment from a domain. Free trial, then $0.02/call."""

    name: str = "mekong_enrich"
    description: str = (
        "Enrich a company from its domain: homepage metadata, DNS, WHOIS, SEC EDGAR. "
        "Public sources only — missing fields come back empty, never hallucinated. "
        "No API key — free daily trial, then $0.02 per call in USDC on Base via x402."
    )
    args_schema: Type[BaseModel] = EnrichArgs

    def _run(self, domain: str) -> str:
        return _fmt_enrich(x402_call("GET", "/enrich/", params={"domain": domain}))


class STTTool(LangChainBaseTool):
    """Speech-to-text transcription. Free trial, then $0.05/call."""

    name: str = "mekong_stt"
    description: str = (
        "Transcribe audio to text from a public audio URL (99+ languages). "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: Type[BaseModel] = STTArgs

    def _run(self, audio_url: str, language: str = "en") -> str:
        return _fmt_stt(
            x402_call(
                "POST",
                "/stt/",
                json_body={"audio_url": audio_url, "language": language},
                timeout=180,
            )
        )


class BriefTool(LangChainBaseTool):
    """Morning-briefing bundle: news + trends + sentiment in one call. Free trial, then $0.05."""

    name: str = "mekong_brief"
    description: str = (
        "One-call morning briefing: market news headlines, Google Trends intel and "
        "news sentiment score for a topic/region. "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: Type[BaseModel] = BriefArgs

    def _run(self, topic: str = "AI agents", geo: str = "US") -> str:
        return _fmt_brief(x402_call("POST", "/brief/", json_body={"topic": topic, "geo": geo}))


class TaskRouterTool(LangChainBaseTool):
    """FREE task router — describe a task, get the right endpoint. Always free, no payment."""

    name: str = "mekong_task_router"
    description: str = (
        "FREE — never costs anything. Describe what you need in plain language and get "
        "the top-3 matching fleet endpoints with prices, paid URLs and ready curls. "
        "Call this first whenever you are unsure which endpoint fits the task."
    )
    args_schema: Type[BaseModel] = TaskRouterArgs

    def _run(self, task: str) -> str:
        return _fmt_recommend(x402_call("POST", "/recommend/", json_body={"task": task}))


__all__ = [
    "WebSearchTool",
    "TokenPriceTool",
    "AIVerdictTool",
    "EnrichTool",
    "STTTool",
    "BriefTool",
    "TaskRouterTool",
]
