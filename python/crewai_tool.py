"""
CrewAI-compatible tools for x402 pay-per-call data APIs.
Trial mode: no wallet, no signup — just run it.

    from crewai import Agent, Task, Crew
    from crewai_tool import X402WebSearchTool, X402NewsTool

    researcher = Agent(
        role="Market Research Analyst",
        goal="Brief me on {topic} with live data",
        tools=[X402WebSearchTool(), X402NewsTool()],
        backstory="You use pay-per-call tools. No API keys needed.",
    )
    task = Task(description="Research {topic}: prices + latest news", agent=researcher,
                expected_output="A short briefing with numbers and headlines")
    Crew(agents=[researcher], tasks=[task]).kickoff(inputs={"topic": "Base chain DeFi"})

For paid calls (after trial quota is exhausted), sign the 402 challenge with
your Base wallet and retry with the X-PAYMENT header (see README).
"""
import requests

BASE = "https://api.mekongtradeintel.com"
UA = {"User-Agent": "x402-agent-demo/1.0 (crewai)"}

try:
    from crewai.tools import BaseTool
    from pydantic import Field
except ImportError:  # pragma: no cover - readable without crewai installed
    class BaseTool:
        pass

    def Field(*a, **k):
        return None


def _post(path, payload):
    r = requests.post(f"{BASE}{path}", json=payload, headers=UA, timeout=30)
    if r.status_code == 402:
        return {"_402": True}
    r.raise_for_status()
    return r.json()


class X402WebSearchTool(BaseTool):
    name: str = "x402_web_search"
    description: str = (
        "Search the live web. No API key — free trial quota, then $0.01/call in USDC (x402)."
    )
    query: str = Field(description="Search query")

    def _run(self, query: str) -> str:
        d = _post("/websearch/api/websearch", {"query": query, "num": 5})
        if d.get("_402"):
            return "Free trial exhausted. Pay $0.01/call in USDC (x402) to continue."
        items = d.get("results") or d.get("items") or []
        return "\n".join(f"- {(it.get('title') or '')[:120]}" for it in items[:5])


class X402NewsTool(BaseTool):
    name: str = "x402_news"
    description: str = (
        "Crypto/tech news headlines with sources. No API key — free trial, then $0.001/call (x402)."
    )
    query: str = Field(description="News topic")

    def _run(self, query: str) -> str:
        d = _post("/news/api/news", {"topic": query})
        if d.get("_402"):
            return "Free trial exhausted. Pay $0.001/call in USDC (x402) to continue."
        items = d.get("results") or d.get("items") or []
        return "\n".join(f"- {(it.get('title') or it.get('headline') or '')[:120]}" for it in items[:5])


if __name__ == "__main__":
    print(X402WebSearchTool()._run("Base chain DeFi"))
    print(X402NewsTool()._run("bitcoin"))
