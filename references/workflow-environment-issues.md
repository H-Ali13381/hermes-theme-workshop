# Workflow Import Failures

Tracebacks observed when launching `python workflow/run.py`. Despite their
appearance, these are almost always **code-level shadowing bugs**, not stale
venvs or upstream version drift.

## Resolved: stdlib `logging` shadowed by `workflow/logging.py` (2026-05-02)

### Symptom

```
File "/.../workflow/run.py", line 32, in <module>
    from langgraph.checkpoint.sqlite import SqliteSaver
  File "/.../site-packages/langchain_core/__init__.py", line 11, in <module>
    from langchain_core._api import (
ImportError: cannot import name 'surface_langchain_deprecation_warnings' from 'langchain_core._api'
  (Did you mean: 'suppress_langchain_deprecation_warning'?)
```

The traceback points at `langchain_core._api`, but `surface_langchain_deprecation_warnings`
is in fact present and importable in a clean interpreter — the error is
misleading.

### Root cause

`python workflow/run.py` causes Python to prepend `workflow/` to `sys.path[0]`.
The skill previously contained `workflow/logging.py`, which shadowed Python's
stdlib `logging` module for every subsequent import in the process. Downstream
packages (`langchain_core`, `langgraph`, `pydantic`) all do `import logging;
logging.getLogger(...)`, which then fails because the workflow file only
exports `get_logger` / `truncate_for_log` and lacks `getLogger`, `Logger`,
`Handler`, etc. The lazy `__getattr__` machinery in `langchain_core._api`
catches the resulting `AttributeError` and re-raises it as the misleading
`ImportError` shown above.

### Fix

`workflow/logging.py` was renamed to `workflow/log_setup.py`, and all 21
import sites in `workflow/`, `workflow/nodes/**`, and
`tests/test_workflow_logging.py` were updated. After the rename
`python workflow/run.py --list` runs cleanly and the full unittest suite
passes.

### Reproduction (kept for diagnostics)

```bash
# Clean interpreter — succeeds:
.venv/bin/python -c "from langgraph.checkpoint.sqlite import SqliteSaver; print('OK')"

# With workflow/ on sys.path[0] — fails iff a stdlib-shadowing module exists there:
.venv/bin/python -c "
import sys
sys.path.insert(0, 'workflow')
from langgraph.checkpoint.sqlite import SqliteSaver
"
```

If the second form fails while the first succeeds, look for a file in
`workflow/` (or whichever directory is being script-launched) whose name
matches a stdlib module: `logging.py`, `json.py`, `tokenize.py`, `typing.py`,
`io.py`, etc.

## Resolved: Step 2.5 FAL image generation fails because `fal-client` is absent (2026-05-03)

### Symptom

The workflow reaches Step 2.5 and emits a generic user-facing interrupt:

```text
⚠  Image generation failed. Proceeding without AI desktop preview.
Check your FAL_KEY and account credits.
```

But the adjacent workflow log contains the real cause:

```text
[WARNING] ricer.visualize: fal_client not installed — image generation unavailable
[WARNING] ricer.visualize: FAL image generation failed — skipping AI desktop preview
```

### Root cause

`workflow/nodes/visualize.py` resolves `FAL_KEY` first, then calls
`_generate_style_image()`, which imports `fal_client`. If the import fails,
the helper returns an empty image URL and the node falls through to the generic
"key/account credits" interrupt. In this case, `FAL_KEY` was resolvable from
the user's shell/Hermes environment; the actual problem was that the skill venv
lacked `fal-client` because `requirements.txt` did not include it, while
`setup.sh` only installs from `requirements.txt`.

### Fix

`fal-client>=0.5.0` belongs in the skill's `requirements.txt` under workflow
dependencies. After adding it, update the existing skill venv from requirements
with explicit user permission:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
uv pip install --python ~/.hermes/skills/creative/linux-ricing/.venv -r ~/.hermes/skills/creative/linux-ricing/requirements.txt
# or, if uv is unavailable:
python3 -m pip install -r ~/.hermes/skills/creative/linux-ricing/requirements.txt
```

### Verification

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
python3 - <<'PY'
import importlib.util, fal_client
print(importlib.util.find_spec('fal_client') is not None)
print(fal_client.__file__)
PY
python3 -m pytest tests/test_env_secret_resolution.py -q
```

Also separately verify the key path, without printing secrets:

```bash
python3 - <<'PY'
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/creative/linux-ricing'))
from workflow.config import resolve_env_secret
print('FAL_KEY', 'set' if resolve_env_secret('FAL_KEY') else 'not set')
PY
```

### Agent behavior

Do not diagnose the generic Step 2.5 interrupt as a key/credit problem until
checking the immediately preceding workflow warnings. If stdout names
`fal_client not installed`, treat it as a dependency packaging/setup failure,
not a fal.ai account issue. The normal workflow Failure Protocol forbids ad-hoc
`pip install`; however, if the user explicitly switches from running a rice
session to fixing the skill code itself, it is appropriate to patch
`requirements.txt`, update the venv, and verify import/tests.

## General guidance

### Do not name modules after stdlib

Any directory that ends up on `sys.path` (either via `python <dir>/<script>.py`
or via an explicit `sys.path.insert`) must not contain `.py` files whose names
collide with stdlib modules. The most error-prone offenders to watch for:
`logging`, `json`, `typing`, `io`, `email`, `string`, `types`, `queue`,
`select`, `signal`, `socket`, `subprocess`, `tokenize`, `warnings`.

### Diagnosing a fresh import failure

Before treating the venv as suspect, run this in order:

1. **Reproduce in a clean interpreter** — does the failing import work via
   `python -c`? If yes, the venv is fine; the failure is a `sys.path` artifact
   of how `workflow/run.py` (or another entry point) is being launched.
2. **List `sys.path[0]`** — `python workflow/run.py` always prepends
   `workflow/`. Check that directory for stdlib name collisions.
3. **Check entry-point `sys.path.insert` calls** — `workflow/run.py` itself
   prepends the skill root and `scripts/`. Check those for collisions too.
4. **Only then** consider an actual venv issue (mismatched langchain_core /
   langgraph versions, partial install, broken pyc cache).

### Agent behavior

Do not respond to import errors of this shape with "the venv is stale, please
re-run setup.sh". That advice is wrong for shadowing bugs and merely defers
the real fix. Walk through the four-step diagnosis above first.

If a real environment-level failure is confirmed (e.g. `pip` reports
unresolvable conflicts on a clean reinstall, or a package is genuinely
missing), surface that as a separate class of failure and ask the user how to
proceed — do not perform `pip install` / `rm -rf .venv` without explicit
permission.

## Related sections

- `references/workflow-llm-errors.md` — model 400/401 / provider-config errors.
- `references/kde-known-issues.md` — post-implementation KDE quirks.
- `SKILL.md` § Failure Protocol.