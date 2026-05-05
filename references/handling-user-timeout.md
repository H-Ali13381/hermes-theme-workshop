# Handling User Input Timeouts

When the workflow reaches a node that requires `input()` (explore, refine, plan, etc.) the agent must:
1. Prompt the user with the exact message from the workflow.
2. Wait for a response. If no response is received within ~30 seconds, send a gentle reminder:
   > "I’m waiting for your answer to the previous prompt. Please reply so we can continue."
3. If the user still does not respond after a second reminder, abort the workflow and surface the pending prompt to the user for manual continuation.

Never send an empty line or a generic “OK” unless the workflow explicitly asks for confirmation. This prevents `EOFError` and keeps the session deterministic.

## Rationale
- The workflow’s `_run_loop` expects a non‑empty string; an empty stdin causes immediate termination.
- Re‑prompting respects the user’s control and avoids silent failures.
- Aligns with the Failure Protocol: report and stop on unexpected behavior.

## Integration
- The bridge script (`references/workflow-bridge-script.md`) already loops on `Command(resume=answer)`. Ensure the answer string is never empty.
- Update any custom bridge scripts to include a timeout guard that calls `input()` with a timeout and falls back to the reminder logic.
