"""langchain-mekong — LangChain partner tools for the Mekong x402 fleet.

37 pay-per-call APIs on Base (USDC). No signup, no API key — your wallet is
the credential. Free daily trial quota on every endpoint.

Quickstart::

    pip install langchain-mekong

    from langchain_mekong import TaskRouterTool, WebSearchTool

    print(TaskRouterTool().run(task="Is this token a honeypot?"))
    print(WebSearchTool().run(query="Ethereum ETF inflows"))

Paid calls raise :class:`X402PaymentRequired` with exact pay instructions
once the free trial quota is exhausted — no silent charges, ever.
"""
from __future__ import annotations

from ._client import X402PaymentRequired
from .tools import (
    AIVerdictTool,
    BriefTool,
    EnrichTool,
    STTTool,
    TaskRouterTool,
    TokenPriceTool,
    WebSearchTool,
)

__all__ = [
    "AIVerdictTool",
    "BriefTool",
    "EnrichTool",
    "STTTool",
    "TaskRouterTool",
    "TokenPriceTool",
    "WebSearchTool",
    "X402PaymentRequired",
]

__version__ = "0.1.0"
