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