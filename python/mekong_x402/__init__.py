"""mekong-x402 — native LangChain / CrewAI tools for the Mekong x402 fleet.

37 pay-per-call APIs on Base (USDC). No signup, no API key — your wallet is
the credential. Free daily trial quota on every endpoint.

Quickstart::

    pip install "mekong-x402[langchain]"   # or [crewai], or [all]

    from mekong_x402.langchain_tools import TaskRouterTool, WebSearchTool

    print(TaskRouterTool().run(task="Is this token a honeypot?"))
    print(WebSearchTool().run(query="Ethereum ETF inflows"))

Paid calls raise :class:`X402PaymentRequired` with exact pay instructions
once the free trial quota is exhausted — no silent charges, ever.
"""
from __future__ import annotations

from . import crewai_tools, langchain_tools
from ._client import BASE_URL, FLEET_WALLET, USDC_BASE, X402PaymentRequired, x402_call
from ._compat import HAS_CREWAI, HAS_LANGCHAIN

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BASE_URL",
    "FLEET_WALLET",
    "USDC_BASE",
    "HAS_CREWAI",
    "HAS_LANGCHAIN",
    "X402PaymentRequired",
    "crewai_tools",
    "langchain_tools",
    "x402_call",
]
