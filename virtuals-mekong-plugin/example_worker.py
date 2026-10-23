"""Example: wire Mekong x402 functions into a G.A.M.E. Worker.

1-command setup:
    pip install game_sdk mekong-x402-game
    export GAME_API_KEY=<your key from https://console.game.virtuals.io/>

Run:
    python example_worker.py
"""
import os

from game_sdk.game.worker import Worker

from mekong_x402 import MEKONG_FUNCTIONS


def get_state_fn(fn_id, action_space):
    # Minimal state — extend with your app's context as needed.
    return {
        "task": "Answer the user's question using the available Mekong x402 functions.",
    }


def main():
    api_key = os.environ.get("GAME_API_KEY")
    if not api_key:
        raise SystemExit("Set GAME_API_KEY first (https://console.game.virtuals.io/)")

    worker = Worker(
        api_key=api_key,
        description=(
            "You are a research assistant with access to the Mekong x402 pay-per-call "
            "API fleet: live web search, morning briefings, token safety verdicts, "
            "company enrichment and token prices. All endpoints offer a free daily "
            "trial; paid calls cost $0.001-$0.05 in USDC on Base. If a function "
            "reports the trial is exhausted, tell the user the exact pay instructions "
            "from the feedback message instead of failing silently."
        ),
        get_state_fn=get_state_fn,
        action_space=MEKONG_FUNCTIONS,
    )

    # Smoke test without an LLM round-trip: call one function directly.
    fn = next(f for f in MEKONG_FUNCTIONS if f.fn_name == "mekong_web_search")
    result = fn.execute(fn_id="smoke", args={"query": {"value": "Base chain TVL"}})
    print("status:", result.action_status)
    print("feedback:", (result.feedback_message or "")[:500])


if __name__ == "__main__":
    main()
