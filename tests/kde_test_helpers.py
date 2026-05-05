"""Small helpers for KDE materializer and undo tests."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
import tempfile
from pathlib import Path
from unittest.mock import patch


@contextmanager
def patched_home(*targets: str | object, home: Path | None = None):
    """Patch one or more module-level HOME constants to an isolated temp home."""
    if home is not None:
        with ExitStack() as stack:
            for target in targets:
                if isinstance(target, str):
                    stack.enter_context(patch(target, home))
                else:
                    stack.enter_context(patch.object(target, "HOME", home))
            yield home
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp_home = Path(tmp)
        with ExitStack() as stack:
            for target in targets:
                if isinstance(target, str):
                    stack.enter_context(patch(target, tmp_home))
                else:
                    stack.enter_context(patch.object(target, "HOME", tmp_home))
            yield tmp_home
