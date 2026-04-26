from __future__ import annotations

import operator
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class RiceSessionState(TypedDict, total=False):
    # Session identity
    session_dir: str        # ~/.config/rice-sessions/<slug>/

    # Progress
    current_step: int       # 1–8

    # Step 1 output
    device_profile: dict    # WM, GPU, screens, apps, chassis type

    # Step 3 output — 10-key palette + metadata
    design: dict

    # Step 4 output
    plan_html_path: str

    # Step 4.5 output
    baseline_ts: str

    # Step 5
    packages: list[str]

    # Step 6 — element loop
    element_queue: list[str]                           # plain list, overwritten each step
    impl_log: Annotated[list[dict], operator.add]      # append-only completed records

    # Conversation history (add_messages deduplicates by id)
    messages: Annotated[list[BaseMessage], add_messages]

    # Non-fatal errors accumulated across steps
    errors: Annotated[list[str], operator.add]
