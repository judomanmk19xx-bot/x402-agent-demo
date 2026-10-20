"""
smolagents Tool subclass for x402 pay-per-call web search.
Trial mode: no wallet, no signup — just run it.

    from smolagents import CodeAgent, InferenceClientModel
    from smolagents_tool import X402WebSearch

    agent = CodeAgent(tools=[X402WebSearch()], model=InferenceClientModel())
    agent.run("What is the latest news about Ethereum ETFs?")

For paid calls (after trial quota is exhausted), sign the 402 challenge with
your Base wallet and retry with the X-PAYMENT header (see README).
"""
import requests

BASE = "https://api.mekongtradeintel.com"
UA = {"User-Agent": "x402-agent-demo/1.0 (smolagents)"}

try:
    from smolagents import Tool
except ImportError:  # pragma: no cover - lets the file import without smolagents
    class Tool:  # minimal stub so the example is readable standalone
        pass


class X402WebSearch(Tool):
    name = "web_search"
    description = (
        "Search the live web. No API key needed — free trial quota applies, "
        "then $0.01 per call in USDC on Base (x402)."
    )
    inputs = {"query": {"type": "string", "description": "Search query"}}
    output_type = "string"

    def forward(self, query: str) -> str:
        r = requests.post(
            f"{BASE}/websearch/api/websearch",
            json={"query": query, "num": 5},
            headers=UA,
            timeout=30,
        )
        if r.status_code == 402:
            return "Free trial exhausted for this IP. Pay $0.01/call in USDC (x402) to continue."
        r.raise_for_status()
        items = r.json().get("results") or r.json().get("items") or []
        return "\n".join(
            f"- {(it.get('title') or it.get('headline') or '')[:120]}"
            for it in items[:5]
        )


class X402TokenPrice(Tool):
    name = "token_price"
    description = (
        "Live token price, market cap and liquidity via DexScreener. "
        "No API key — free trial, then $0.001 per call in USDC (x402)."
    )
    inputs = {
        "chain": {"type": "string", "description": 'Chain, e.g. "base"'},
        "address": {"type": "string", "description": "Token contract address (0x...)"},
    }
    output_type = "string"

    def forward(self, chain: str, address: str) -> str:
        r = requests.post(
            f"{BASE}/tokenprice/api/token-price",
            json={"chain": chain, "address": address},
            headers=UA,
            timeout=30,
        )
        if r.status_code == 402:
            return "Free trial exhausted for this IP. Pay $0.001/call in USDC (x402) to continue."
        r.raise_for_status()
        d = r.json()
        return f"{d.get('token', {}).get('symbol')}: ${d.get('priceUsd')} | mcap ${d.get('marketCap')} | 24h vol ${d.get('volume24hUsd')}"


if __name__ == "__main__":
    print(X402WebSearch().forward("Ethereum ETF news"))
    print(X402TokenPrice().forward("base", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"))
