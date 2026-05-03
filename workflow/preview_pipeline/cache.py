from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def pending_preview_path(session_dir: str) -> Path:
    return Path(session_dir).expanduser() / "visualize.pending.json"


def load_pending_preview(session_dir: str) -> dict[str, Any]:
    path = pending_preview_path(session_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    if not isinstance(data.get("image_url"), str):
        return {}
    if not isinstance(data.get("visual_context"), dict):
        data["visual_context"] = {}
    return data


def save_pending_preview(session_dir: str, image_url: str, html_path: Path, visual_context: dict) -> None:
    path = pending_preview_path(session_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "image_url": image_url,
        "html_path": str(html_path),
        "visual_context": visual_context if isinstance(visual_context, dict) else {},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_pending_preview(session_dir: str) -> None:
    pending_preview_path(session_dir).unlink(missing_ok=True)


def preview_history_path(session_dir: str) -> Path:
    return Path(session_dir).expanduser() / "preview_pipeline.history.jsonl"


def append_preview_history(session_dir: str, entry: dict) -> None:
    path = preview_history_path(session_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_preview_history(session_dir: str) -> list[dict]:
    path = preview_history_path(session_dir)
    rows: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    except Exception:
        return []
    return rows
