# Programmatic Workflow Bridge

The LangGraph workflow uses `input()` at every interrupt gate (Steps 2, 4, 5, 6, 8).
When launched via the agent's terminal tool with `pty=true`, the process gets `EOFError`
on stdin and exits cleanly — it cannot receive interactive input from the agent.

**Symptom:** Workflow prints a prompt, immediately says "Session paused. Resume with: ...",
and the terminal call returns. The prompt never waited for input.

## Solution: `rice_bridge.py`

A small wrapper script that loads the graph from the SQLite checkpointer and feeds
answers via `Command(resume=...)`. The agent writes answers to a temp file or passes
them as CLI arguments.

### Template

```python
#!/usr/bin/env python3
"""Bridge between chat agent and LangGraph interrupt."""
import sys, os, json
from pathlib import Path
SKILL_DIR = Path(os.path.expanduser("~/.hermes/skills/creative/linux-ricing"))
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from workflow.config import DB_PATH
from workflow.graph import build_graph

def pending_interrupts(state):
    pending = []
    for task in state.tasks:
        for interrupt in getattr(task, "interrupts", []):
            pending.append(interrupt.value)
    return pending

def session_status(state):
    pending_msgs = []
    for val in pending_interrupts(state):
        if isinstance(val, dict):
            pending_msgs.append({
                "step": val.get("step"),
                "type": val.get("type"),
                "element": val.get("element"),
                "score": val.get("score"),
                "message": val.get("message"),
            })
        else:
            pending_msgs.append({"message": str(val)})
    values = state.values or {}
    queue = list(values.get("element_queue") or [])
    compact = {k: values[k] for k in ("current_step", "session_dir") if k in values}
    if queue:
        compact["queue_head"] = queue[:5]
        compact["queue_len"] = len(queue)
    if isinstance(values.get("design"), dict):
        compact["design_name"] = values["design"].get("name")
    if isinstance(values.get("device_profile"), dict):
        dp = values["device_profile"]
        compact["device_profile"] = {k: dp.get(k) for k in ("wm", "session_type", "desktop_recipe") if k in dp}
    if values.get("errors"):
        compact["errors_count"] = len(values["errors"])
    return {
        "next": list(state.next) if state.next else [],
        "values": compact,
        "pending_messages": pending_msgs,
    }

def main():
    thread_id = sys.argv[1] if len(sys.argv) > 1 else None
    answer = sys.argv[2] if len(sys.argv) > 2 else None

    if not thread_id:
        print("Usage: python3 rice_bridge.py <thread_id> [answer]", file=sys.stderr)
        sys.exit(1)

    config = {"configurable": {"thread_id": thread_id}}

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)

        state = graph.get_state(config)
        pending = pending_interrupts(state)

        if answer is None and pending:
            # Read-only status check. Do NOT call graph.stream(None) while an
            # interrupt is pending: for non-idempotent nodes like visualize,
            # streaming with no Command can re-enter the node and regenerate
            # assets before the user has answered the previous gate.
            print(json.dumps(session_status(state), indent=2, default=str))
            sys.exit(0)

        if answer is not None and not pending:
            result = session_status(state)
            result["error"] = (
                f"Cannot resume with answer {answer!r}: session has no pending "
                f"interrupt (next={result['next']}). Run without an answer to "
                "check status, or wait until pending_messages is non-empty."
            )
            print(json.dumps(result, indent=2, default=str))
            sys.exit(2)

        current_input = Command(resume=answer) if answer is not None else None

        try:
            for chunk in graph.stream(current_input, config, stream_mode="updates"):
                pass  # chunks printed by graph
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)

        state = graph.get_state(config)
        result = session_status(state)
        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
```

### Usage Pattern

`workflow.config.resolve_llm_config()` auto-resolves model, base URL, API key, and
api_mode from `~/.hermes/config.yaml` + `~/.hermes/.env`. **No `RICER_*` env vars
are required** as long as Hermes is configured. Use the simple form:

```bash
# 1. Check current state (no answer — just read the pending interrupt)
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
python3 /tmp/rice_bridge.py <thread-id>

# 2. Feed an answer (the explore node loops: brief → propose → finalize)
python3 /tmp/rice_bridge.py <thread-id> "user's answer here"

# 3. Repeat — each call advances one interrupt gate
```

The bridge refuses an answer when `pending_messages` is empty. This prevents
control words such as `skip` from accidentally starting normal graph execution
when there is no score gate or approval prompt to answer.

#### When to set `RICER_*` env vars

`RICER_BASE_URL`, `RICER_API_KEY`, `RICER_MODEL` are **opt-in overrides** — set
them only when you need to bypass the active Hermes config (e.g. testing a
different model, or running against a non-Hermes machine). Each takes priority
over its Hermes-config equivalent when non-empty. Resolution precedence is
covered by `tests/test_llm_config_resolution.py`.

```bash
# Example override: run one bridge call against a different model.
RICER_MODEL="some/other-model" python3 /tmp/rice_bridge.py <thread-id>
```

### Pitfall: Multi-line Answers

The bridge script takes the answer as a single CLI argument. Shell quoting of
multi-line creative briefs (especially those containing newlines, quotes, or
bullets) is fragile and often results in truncated or mangled input.

**Reliable pattern:** write the answer to a temp file, then pass it via command
substitution:

```bash
# Write the user's answer to a file
cat > /tmp/rice_answer.txt << 'EOF'
1. An inn at the edge of time, RPG aesthetic, the final place to rest & test your skills.
2. Place to rest and relax, before the final challenge.
3. 2000s flash games, RPGs, dark souls, old school RPGs, Skyrim, elden ring, Dragonfable, Adventurequest world. Game menu aesthetic.
4. Avoid pixel art, let's go for a clean aesthetic. I want RPG inspired menus, not KDE default color swaps
EOF

# Feed it to the bridge
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
ANSWER=$(cat /tmp/rice_answer.txt) && python3 /tmp/rice_bridge.py <thread-id> "$ANSWER"
```

This avoids all shell-escaping pitfalls and preserves formatting exactly.

### Pitfall: Exit Code 130 / Command Interrupted

If the bridge returns exit code 130 with `[Command interrupted]` in stderr, the graph
stream hit an interrupt mid-execution and exited. This is normal — it means the graph
processed one element and hit a score gate or other interrupt.

**What to do:** Call the bridge again with no answer to read the current state:
```bash
python3 /tmp/rice_bridge.py <thread-id>
```
The JSON output will show `pending_messages` with the gate prompt. Then feed the
appropriate answer ("retry", "accept", "skip", or a description of changes).

**Critical:** the no-answer status call must be read-only when `pending_messages` is
already non-empty. Older bridge templates called `graph.stream(None)` even with a
pending interrupt; on Step 2.5 this re-entered `visualize` and generated a second FAL
image/analysis, replacing the approval target before the user answered. Use the template
above, which prints `session_status(state)` and exits immediately if `answer is None`
and an interrupt is pending.

**Do NOT re-send the previous answer** — the interrupt is already consumed. Read the
state first, then answer what's actually pending.

### Important Notes

- The bridge outputs JSON. Parse `pending_messages[0].message` for the next prompt.
- Do not pass an answer unless `pending_messages` is non-empty; the bridge exits
  with code 2 if there is no pending interrupt to consume the answer.
- The explore node has 3 stages: brief, propose, finalize. Each requires a separate
  bridge call with the user's answer.
  - Stage 1 (brief): send the user's raw creative brief (place/mood/reference/avoid).
  - Stage 2 (propose): the workflow proposes 3 named directions; user picks one, combines,
    or refines in prose — the workflow accepts free-form, not just "1/2/3".
  - Stage 3 (finalize): workflow emits `[Explore] Direction confirmed:` in stdout and
    transitions to refine WITHOUT another bridge interrupt. No third call needed.
- After explore finishes, the refine node may emit `[Refine][WARN] Sentinel found but
  design JSON could not be parsed` immediately (even on the first attempt). Do NOT feed
  more bridge answers — go straight to the state injection bypass (see main SKILL.md).
- LLM calls inside the bridge can take 60-120s+ via OpenRouter. Use timeout=300.
- The bridge script must be run with the skill's venv activated.
- Write the bridge to `/tmp/rice_bridge.py` at session start — it's disposable.

### Pitfall: sudo_password Interrupts

The `install` node (Step 5) uses a `sudo_password` interrupt type. The bridge CANNOT
handle this securely — passing the password as a CLI argument would expose it in
terminal output and process listings.

**When the workflow hits a sudo_password interrupt via the bridge:**
1. The bridge will return JSON with `pending_messages[0].type == "sudo_password"`
2. Option A (preferred): Feed the answer "skip" via the bridge to skip the package, then install it manually with `sudo pacman -S <package>` from the agent terminal.
3. Option B: Tell the user to run the workflow directly in their terminal:
   ```bash
   source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate && \
     python3 ~/.hermes/skills/creative/linux-ricing/workflow/run.py --resume <thread-id>
   ```
4. The user enters their password securely via the terminal's masked prompt
5. After the workflow passes the install step, the agent can resume using the bridge

**Note:** The agent terminal CAN run sudo directly (unlike the bridge). If the workflow
skipped a package due to sudo, install it manually with `sudo pacman -S <package>` or
`sudo pacman -U <built-pkg>` from the agent terminal, then continue the workflow.
