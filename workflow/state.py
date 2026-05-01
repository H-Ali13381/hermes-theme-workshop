from __future__ import annotations

import operator
from typing import Annotated

try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore[assignment]  # Python 3.8+ built-in

try:
    from langchain_core.messages import BaseMessage
    from langgraph.graph.message import add_messages
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    from typing import Any as BaseMessage  # type: ignore[assignment]

    def add_messages(left: list, right: list) -> list:  # type: ignore[misc]
        return (left or []) + (right or [])


class RiceSessionState(TypedDict, total=False):
    # Session identity
    session_dir: str        # ~/.config/rice-sessions/<slug>/

    # Progress
    current_step: int       # 1–8

    # Step 1 output
    device_profile: dict    # WM, GPU, screens, apps, chassis type

    # Step 3 output — 10-key palette + metadata
    design: dict

    # Step 2 fast intake state. Keeps creative exploration structured so the
    # user experiences one direct chat instead of visible agent handoffs.
    explore_intake: dict

    # Step 4 output
    plan_html_path: str

    # Step 4.5 output
    baseline_ts: str

    # Step 5
    packages: list[str]

    # Step 6 — element loop
    element_queue: list[str]                           # plain list, overwritten each step
    impl_log: Annotated[list[dict], operator.add]      # append-only completed records
    impl_retry_counts: dict                            # element → retry attempts so far

    # Step 7 — deterministic cleanup/finalization actions performed after Step 6.
    cleanup_actions: Annotated[list[dict], operator.add]
    effective_state: dict
    capability_report: dict
    visual_artifacts: Annotated[list[dict], operator.add]

    # Loop-safety: counts how many times each looping node has been invoked.
    # Keys: "explore", "refine", "plan".  Routing functions check these against
    # MAX_LOOP_ITERATIONS and abort to END when the limit is reached, preventing
    # infinite LLM loops when a sentinel is emitted with unparseable JSON.
    loop_counts: dict

    # Conversation history (add_messages deduplicates by id)
    messages: Annotated[list[BaseMessage], add_messages]

    # Non-fatal errors accumulated across steps
    errors: Annotated[list[str], operator.add]
