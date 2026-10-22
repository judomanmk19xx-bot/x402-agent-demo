"""CrewAI-native tools for the Mekong x402 fleet.

    from crewai import Agent
    from mekong_x402.crewai_tools import WebSearchTool, TaskRouterTool

    analyst = Agent(
        role="Research Analyst",
        goal="Brief me with live data",
        tools=[WebSearchTool(), TaskRouterTool()],
        backstory="You use pay-per-call tools. No API keys needed.",
    )

Requires ``pip install mekong-x402[crewai]`` for production use;
imports cleanly without crewai (shim) for inspection/testing.

Follows the crewai-tools repo convention: ``args_schema`` pydantic models
+ ``_run(**kwargs)`` (cf. BraveSearchTool upstream).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from ._client import x402_call
from ._compat import CrewAIBaseTool
from .langchain_tools import (
    AIVerdictArgs,
    BriefArgs,
    EnrichArgs,
    STTArgs,
    TaskRouterArgs,
    TokenPriceArgs,
    WebSearchArgs,
    _fmt_aiverdict,
    _fmt_brief,
    _fmt_enrich,
    _fmt_recommend,
    _fmt_search,
    _fmt_stt,
    _fmt_tokenprice,
)


class WebSearchTool(CrewAIBaseTool):
    name: str = "mekong_web_search"
    description: str = (
        "Search the live web and get deduped, relevance-scored results. "
        "No API key needed — free daily trial, then $0.01 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = WebSearchArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_search(
            x402_call("POST", "/websearch/",
                      json_body={"query": kwargs["query"], "num": kwargs.get("num", 5)})
        )


class TokenPriceTool(CrewAIBaseTool):
    name: str = "mekong_token_price"
    description: str = (
        "Live token price, market cap, 24h volume and liquidity. "
        "Use chain+address for exact lookup (ticker alone can be ambiguous). "
        "No API key — free daily trial, then $0.001 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = TokenPriceArgs

    def _run(self, **kwargs: Any) -> str:
        if kwargs.get("address"):
            body: dict = {"address": kwargs["address"]}
            if kwargs.get("chain"):
                body["chain"] = kwargs["chain"]
        elif kwargs.get("ticker"):
            body = {"ticker": kwargs["ticker"]}
        else:
            raise ValueError("Provide ticker, or chain+address.")
        return _fmt_tokenprice(x402_call("POST", "/tokenprice/", json_body=body))


class AIVerdictTool(CrewAIBaseTool):
    name: str = "mekong_ai_verdict"
    description: str = (
        "AI verdict on whether a token is safe: honeypot/tax/owner screening plus "
        "liquidity checks, with written reasoning. Not financial advice. "
        "No API key — free daily trial, then $0.01 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = AIVerdictArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_aiverdict(x402_call("POST", "/aiverdict/", json_body={"query": kwargs["query"]}))


class EnrichTool(CrewAIBaseTool):
    name: str = "mekong_enrich"
    description: str = (
        "Enrich a company from its domain: homepage metadata, DNS, WHOIS, SEC EDGAR. "
        "Public sources only — missing fields come back empty, never hallucinated. "
        "No API key — free daily trial, then $0.02 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = EnrichArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_enrich(x402_call("GET", "/enrich/", params={"domain": kwargs["domain"]}))


class STTTool(CrewAIBaseTool):
    name: str = "mekong_stt"
    description: str = (
        "Transcribe audio to text from a public audio URL (99+ languages). "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = STTArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_stt(
            x402_call(
                "POST", "/stt/",
                json_body={"audio_url": kwargs["audio_url"],
                           "language": kwargs.get("language", "en")},
                timeout=180,
            )
        )


class BriefTool(CrewAIBaseTool):
    name: str = "mekong_brief"
    description: str = (
        "One-call morning briefing: market news headlines, Google Trends intel and "
        "news sentiment score for a topic/region. "
        "No API key — free daily trial, then $0.05 per call in USDC on Base via x402."
    )
    args_schema: type[BaseModel] = BriefArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_brief(
            x402_call("POST", "/brief/",
                      json_body={"topic": kwargs.get("topic", "AI agents"),
                                 "geo": kwargs.get("geo", "US")})
        )


class TaskRouterTool(CrewAIBaseTool):
    name: str = "mekong_task_router"
    description: str = (
        "FREE — never costs anything. Describe what you need in plain language and get "
        "the top-3 matching fleet endpoints with prices, paid URLs and ready curls. "
        "Call this first whenever you are unsure which endpoint fits the task."
    )
    args_schema: type[BaseModel] = TaskRouterArgs

    def _run(self, **kwargs: Any) -> str:
        return _fmt_recommend(x402_call("POST", "/recommend/", json_body={"task": kwargs["task"]}))


__all__ = [
    "WebSearchTool",
    "TokenPriceTool",
    "AIVerdictTool",
    "EnrichTool",
    "STTTool",
    "BriefTool",
    "TaskRouterTool",
]
