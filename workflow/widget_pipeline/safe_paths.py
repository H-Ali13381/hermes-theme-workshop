"""Safe artifact path helpers for widget pipeline dry-run outputs."""

from __future__ import annotations

from pathlib import Path
import re

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")


def safe_artifact_path(base_dir: str | Path, artifact_id: str, suffix: str) -> Path:
    """Return a safe child path for an artifact id.

    The widget pipeline eventually consumes model/segmentation-produced ids. Keep
    ids as stable contract identifiers, but never interpolate unchecked ids into
    filesystem paths. This helper rejects slashes, parent traversal, empty ids,
    and shell-ish punctuation, then verifies the resolved artifact remains under
    ``base_dir``.
    """

    base = Path(base_dir)
    safe_id = str(artifact_id).strip()
    if not _SAFE_ID_RE.fullmatch(safe_id):
        raise ValueError(f"unsafe widget artifact id: {artifact_id!r}")
    if not suffix.startswith("."):
        raise ValueError(f"artifact suffix must start with '.': {suffix!r}")

    base_resolved = base.resolve()
    path = (base / f"{safe_id}{suffix}").resolve()
    if path.parent != base_resolved:
        raise ValueError(f"artifact path escapes output directory: {path}")
    return path
