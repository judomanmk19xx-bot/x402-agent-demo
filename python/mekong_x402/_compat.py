"""Optional-dependency shims.

langchain-core and crewai are *optional* extras (``pip install mekong-x402[all]``).
When they are missing, we fall back to tiny local base classes so the package
still imports and the tools stay readable/testable. Install the real frameworks
for production use.
"""
from __future__ import annotations

try:  # real LangChain
    from langchain_core.tools import BaseTool as LangChainBaseTool

    HAS_LANGCHAIN = True
except ImportError:  # pragma: no cover

    HAS_LANGCHAIN = False

    class LangChainBaseTool:  # minimal shim: name/description/args_schema/_run
        name: str = ""
        description: str = ""
        args_schema = None

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def run(self, *args, **kwargs):
            return self._run(*args, **kwargs)

        def _run(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError


try:  # real CrewAI
    from crewai.tools import BaseTool as CrewAIBaseTool

    HAS_CREWAI = True
except ImportError:  # pragma: no cover

    HAS_CREWAI = False

    class CrewAIBaseTool:  # minimal shim: pydantic-style field defaults
        name: str = ""
        description: str = ""

        def __init__(self, **kwargs):
            # collect Field() defaults declared as class attributes
            for cls in reversed(type(self).__mro__):
                for k, v in vars(cls).get("__annotations__", {}).items():
                    if k not in kwargs and hasattr(cls, k):
                        default = getattr(cls, k)
                        if default is not None:
                            setattr(self, k, default)
            for k, v in kwargs.items():
                setattr(self, k, v)

        def run(self, *args, **kwargs):
            return self._run(*args, **kwargs)

        def _run(self, *args, **kwargs):  # pragma: no cover
            raise NotImplementedError
