# PR materials — notes & blockers

## Conventions verified (from live repo reads, 2026-10-22)

**crewai-tools** (now inside the `crewAIInc/crewAI` monorepo):
- Path: `lib/crewai-tools/src/crewai_tools/tools/<tool_name>/`
- Files per tool: `<tool_name>.py` + `schemas.py` (+ `base.py` when shared logic) + `README.md`
- Pattern (verified against `brave_search_tool/brave_search_tool.py` @ main):
  `from crewai.tools import BaseTool, EnvVar` → `args_schema: type[BaseModel]` →
  `_run(self, **kwargs)`. Required API keys declared via `env_vars: list[EnvVar]`.
- Our material mirrors this exactly. We declare **no** `env_vars` (no API key exists —
  that is the x402 pitch) and say so in the PR body.

**langchain-community** (`langchain-ai/langchain-community`):
- Path: `libs/community/langchain_community/tools/<tool_name>/` (`tool.py` + `__init__.py`)
- Pattern (verified against `tools/brave_search/tool.py` @ main):
  `langchain_core.tools.BaseTool` subclass, `name`/`description`, pydantic
  `args_schema`, `_run(self, query, run_manager=None)`, docstring with examples.
- New tools must also be registered in `tools/__init__.py` (not shipped here —
  one-line addition by the PR author at submit time).

## Blockers / open items

1. **No GitHub auth in this environment** (`gh` not logged in) → PRs **not submitted**,
   per task instructions (prep only). To submit: `gh auth login`, fork both repos,
   copy the material dirs into place, open PRs with the provided bodies.
2. **langchain-community intake policy (UNVERIFIED):** LangChain has been steering
   new integrations toward partner packages (`langchain-x-<name>`) rather than
   `langchain-community`. Check their current CONTRIBUTING before submitting;
   the PR body already offers the partner-package alternative to reviewers.
3. **CrewAI real-framework bug found & fixed during testing:** the pre-existing
   `python/crewai_tool.py` in this repo declares `query: str = Field(...)` with no
   default → pydantic ValidationError on `Tool()` with real `crewai.tools.BaseTool`
   (verified against crewai 1.15.28). Our package + PR materials use the
   `args_schema` + `_run(**kwargs)` pattern (same as upstream BraveSearchTool),
   which instantiates cleanly. The old `crewai_tool.py` is kept as-is (example file);
   consider updating it or pointing its docstring at `mekong_x402`.
4. **npm-style registry not applicable:** Python only; no PyPI publish attempted
   (needs `twine` + PyPI token — user decision).
5. **Paid paths never executed** in tests (by design): 402 handling is unit-tested
   with mocked responses; only free endpoints (`/recommend`, trial-eligible GETs)
   were hit live.
