# Workflow LLM Error Patterns

Session-specific reference for errors thrown by `workflow/run.py` during LLM node execution (explore, refine, plan, handoff).

---

## Pattern 1: Invalid Model ID (400)

**First seen:** 2026-04-30 — OpenRouter provider, model fallback bug.

**Traceback signature:**
```
openai.BadRequestError: Error code: 400 - {
  'error': {
    'message': 'claude-sonnet-4-5-20251029 is not a valid model ID',
    'code': 400
  }
}
```
Occurs in `explore_node` (Step 2) or any node that calls `get_llm()`.

**Two simultaneous defects in `workflow/config.py`:**

1. **Hardcoded fallback model is provider-invalid.**
   ```python
   # BEFORE (broken) — Anthropic-native shorthand, invalid on OpenRouter
   MODEL = os.environ.get("RICER_MODEL", "claude-sonnet-4-5-20251029")
   ```
   Fix: use a valid OpenAI-compatible identifier for the user's provider:
   ```python
   # AFTER — valid on OpenRouter
   MODEL = os.environ.get("RICER_MODEL", "deepseek/deepseek-v4-pro")
   ```

2. **Env vars short-circuit Hermes config loading.**
   ```python
   # BEFORE (broken) — only loads Hermes config when BOTH env vars missing
   if not (base_url and api_key):
       h = _load_hermes_config()
       ...
       if not os.environ.get("RICER_MODEL") and h.get("model"):
           model = h["model"]
   ```
   When the agent passes `RICER_API_KEY` + `RICER_BASE_URL` to fix auth, `h["model"]` is never read, so the invalid fallback is used.

   Fix: always load Hermes config, let env vars override individual fields:
   ```python
   # AFTER
   h = _load_hermes_config()
   base_url = base_url or h.get("base_url", "")
   api_key  = api_key  or h.get("api_key",  "")
   api_mode = h.get("api_mode", "")
   if not model and h.get("model"):
       model = h["model"]
   if not model:
       model = MODEL
   ```

**Quick workaround without editing code:**
```bash
RICER_MODEL="deepseek/deepseek-v4-pro" \
  RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
  RICER_BASE_URL="https://openrouter.ai/api/v1" \
  python3 workflow/run.py
```

---

## Pattern 2: Authentication Failure (401)

**Symptoms:** `openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}` during Step 2+ (any LLM call).

**Resolution priority used by `get_llm()` in `workflow/config.py`:**
1. `RICER_API_KEY` / `RICER_BASE_URL` env vars (bypass all file-based config)
2. `config.yaml` → `providers.<provider>.api_key` (inline key)
3. `~/.hermes/.env` → `<PROVIDER>_API_KEY` (only if step 2 returned empty)

**Known pitfall:** If `config.yaml` has a *stale* non-empty API key, the workflow uses it and never falls back to `.env`. The stale key may have worked at setup time but since been rotated. Hermes itself may resolve keys differently (credential pool, system env), so the main chat works while the workflow fails with 401.

**Diagnose:** Compare the two key sources:
```bash
python3 -c "
import sys; sys.path.insert(0, '<skill-dir>')
from workflow.config import _load_hermes_config, _parse_dotenv
from pathlib import Path
h = _load_hermes_config()
env = _parse_dotenv(Path.home() / '.hermes' / '.env')
print(f'config.yaml key length: {len(h[\"api_key\"])}')
print(f'.env key length: {len(env.get(\"OPENROUTER_API_KEY\", \"\"))}')
print(f'Keys match: {h[\"api_key\"] == env.get(\"OPENROUTER_API_KEY\", \"\")}')
"
```
If keys differ, the `.env` key is the working one.

**Fix:** Pass the working key via env var when launching or resuming:
```bash
RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
  python3 workflow/run.py [--resume <thread-id>]
```
Or set `RICER_API_KEY` + `RICER_BASE_URL` permanently in your shell profile.

---

## Verification snippet

Run this before launching the workflow to confirm the resolved model is valid:
```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/creative/linux-ricing'))
from workflow.config import get_llm
llm = get_llm()
print('Model:', getattr(llm, 'model_name', getattr(llm, 'model', 'unknown')))
print('Base URL:', getattr(llm, 'openai_api_base', getattr(llm, 'base_url', 'default')))
"
```
