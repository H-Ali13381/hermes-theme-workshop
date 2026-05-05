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
RICER_API_KEY="<provider-api-key>" \
  RICER_BASE_URL="https://openrouter.ai/api/v1" \
  RICER_MODEL="deepseek/deepseek-v4-pro" \
  python3 workflow/run.py [--resume <thread-id>]
```

---

## Pattern 2: Authentication Failure (401)

**Symptoms:** `openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}` during Step 2+ (any LLM call).

**Resolution priority used by `get_llm()` in `workflow/config.py`:**
1. `RICER_API_KEY` / `RICER_BASE_URL` env vars (explicit overrides)
2. `~/.hermes/config.yaml` active provider fields plus `~/.hermes/.env` provider key
   - `.env` provider keys override inline provider keys because inline keys often go stale
3. If the active Hermes provider is `openai-codex`, the workflow uses Hermes Agent's OAuth path: refresh through `hermes_cli.auth.resolve_codex_runtime_credentials()`, then call `agent.auxiliary_client.resolve_provider_client("openai-codex", model=...)` and its Codex Responses streaming adapter.

**Known pitfall:** The ChatGPT Codex backend requires the OAuth bearer token and Responses streaming behaviour that Hermes Agent already implements. Do not construct `ChatOpenAI` directly against `https://chatgpt.com/backend-api/codex`; use the Hermes OAuth adapter path above, or explicit `RICER_*` overrides for another provider.

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

**Fix:** Current code should use the Hermes OAuth adapter automatically when `openai-codex` is active. To force a specific provider/model when launching or resuming, pass explicit overrides:
```bash
RICER_API_KEY="<openrouter-api-key>" \
  RICER_BASE_URL="https://openrouter.ai/api/v1" \
  RICER_MODEL="deepseek/deepseek-v4-pro" \
  python3 workflow/run.py [--resume <thread-id>]
```
Or set `RICER_API_KEY` + `RICER_BASE_URL` + `RICER_MODEL` permanently in your shell profile.

---

## Pattern 3: Text-only LLM shim lacks structured output in Step 6 implement spec

**First seen:** 2026-05-03 — active Hermes provider `openai-codex` / `gpt-5.5`, using the Codex Responses OAuth adapter.

**Traceback / score signature:** Step 6 `implement` repeatedly produces an empty or useless `ElementSpec`, then the element scores around 2/10. The spec notes may include:
```json
{
  "targets": [],
  "palette_keys": [],
  "font": "N/A",
  "radii": "N/A",
  "notes": "'_CodexOAuthLLM' object has no attribute 'with_structured_output'"
}
```

**Root cause:** `workflow/nodes/implement/spec.py` assumed every configured LLM supports LangChain's `with_structured_output(ElementSpec)`. Hermes' `openai-codex` OAuth shim intentionally exposes the simpler `invoke(...)` interface, so structured-output-only consumers fail even though normal text generation works.

**Fix pattern:** Adapt the consumer, not the OAuth shim. In `write_spec(...)`:
1. Try `llm.with_structured_output(ElementSpec).invoke(...)` for providers that support it.
2. Catch only `AttributeError` and `NotImplementedError` for missing structured-output support.
3. Fall back to `llm.invoke(...)` with a JSON-only system prompt that describes the exact `ElementSpec` schema.
4. Extract JSON defensively from raw text or ```json fenced output.
5. Validate into `ElementSpec`; only return the safe empty spec if both structured and JSON-text paths fail.

**Regression test pattern:** Add a fake LLM that implements `invoke(...)` but no `with_structured_output(...)`; assert `write_spec(...)` returns non-empty `targets` and `palette_keys`. Also keep the normal structured-output test to preserve parity for LangChain providers.

**Manual verification snippet:**
```bash
cd ~/.hermes/skills/creative/linux-ricing
source .venv/bin/activate
python3 - <<'PY'
from workflow.nodes.implement.spec import write_spec
from workflow.state import RiceState
state = RiceState(theme='verification', design={'palette': {'background': '#000000', 'foreground': '#ffffff', 'accent': '#cc8844'}})
spec = write_spec('terminal:kitty', state)
print(spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict())
PY
```
Expected: `targets` should include kitty config paths and `palette_keys` should include real palette entries; it should not be an all-empty fallback with a `with_structured_output` error.

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
