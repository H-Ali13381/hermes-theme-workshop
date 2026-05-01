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

def main():
    thread_id = sys.argv[1] if len(sys.argv) > 1 else None
    answer = sys.argv[2] if len(sys.argv) > 2 else None

    if not thread_id:
        print("Usage: python3 rice_bridge.py <thread_id> [answer]", file=sys.stderr)
        sys.exit(1)

    config = {"configurable": {"thread_id": thread_id}}

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)

        if answer is not None:
            current_input = Command(resume=answer)
        else:
            current_input = None

        try:
            for chunk in graph.stream(current_input, config, stream_mode="updates"):
                pass  # chunks printed by graph
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)

        state = graph.get_state(config)

        result = {
            "next": list(state.next) if state.next else [],
            "values": {k: v for k, v in state.values.items() if k in (
                "current_step", "explore_intake", "design", "element_queue",
                "device_profile", "session_dir"
            )},
        }

        pending_msgs = []
        for task in state.tasks:
            for interrupt in getattr(task, "interrupts", []):
                val = interrupt.value
                if isinstance(val, dict):
                    pending_msgs.append({
                        "step": val.get("step"),
                        "type": val.get("type"),
                        "message": val.get("message"),
                    })
                else:
                    pending_msgs.append({"message": str(val)})

        result["pending_messages"] = pending_msgs
        print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
```

### Usage Pattern

```bash
# 1. Check current state (no answer — just read the pending interrupt)
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
RICER_BASE_URL="https://openrouter.ai/api/v1" \
RICER_MODEL="deepseek/deepseek-v4-pro" \
  python3 /tmp/rice_bridge.py <thread-id>

# 2. Feed an answer (the explore node loops: brief → propose → finalize)
RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
RICER_BASE_URL="https://openrouter.ai/api/v1" \
RICER_MODEL="deepseek/deepseek-v4-pro" \
  python3 /tmp/rice_bridge.py <thread-id> "user's answer here"

# 3. Repeat — each call advances one interrupt gate
```

> **Note:** Check your `~/.hermes/config.yaml` for the correct model name under
> `providers.<provider>.model`. The model must be a valid identifier for your provider.

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

**Do NOT re-send the previous answer** — the interrupt is already consumed. Read the
state first, then answer what's actually pending.

### Important Notes

- The bridge outputs JSON. Parse `pending_messages[0].message` for the next prompt.
- The explore node has 3 stages: brief, propose, finalize. Each requires a separate
  bridge call with the user's answer.
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
