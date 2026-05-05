"""Safety-net tests for planned repository hygiene improvements.

These tests intentionally encode the desired invariants before the cleanup work:
dependency metadata should stay in sync, documentation should not drift from
source data, live desktop mutation tests must be opt-in, and production
subprocess calls that decode text should be locale-independent.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _preset_names() -> list[str]:
    tree = ast.parse((ROOT / "scripts" / "presets.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "PRESETS" and isinstance(node.value, ast.Dict):
                return [key.value for key in node.value.keys if isinstance(key, ast.Constant)]
    raise AssertionError("PRESETS dict not found in scripts/presets.py")


_DEV_SECTION_HEADERS = ("tests", "test", "dev", "development")


def _runtime_requirements() -> set[str]:
    """Parse requirements.txt, skipping packages under dev-only section headers.

    Section headers are ``# <name>`` comment lines; e.g. ``# tests`` marks every
    subsequent package as test-only until the next non-test header or blank-line
    reset.  This mirrors how the file is hand-organised so dev-only deps like
    ``pytest`` aren't required to appear in ``manifest.json``'s runtime list.
    """
    runtime: set[str] = set()
    section_is_runtime = True
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped:
            section_is_runtime = True
            continue
        if stripped.startswith("#"):
            label = stripped.lstrip("#").strip().lower()
            section_is_runtime = label not in _DEV_SECTION_HEADERS
            continue
        if not section_is_runtime:
            continue
        runtime.add(stripped.split("==", 1)[0].split(">=", 1)[0].lower())
    return runtime


def test_manifest_runtime_packages_cover_script_requirements() -> None:
    requirements = _runtime_requirements()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    manifest_packages = {
        pkg.split("==", 1)[0].split(">=", 1)[0].lower()
        for pkg in manifest["requirements"]["packages"]
    }

    missing = sorted(requirements - manifest_packages)
    assert missing == [], f"manifest.json is missing runtime package(s): {missing}"


def test_readme_preset_count_matches_presets_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    preset_count = len(_preset_names())

    stale_counts = []
    for match in re.finditer(r"presets\.py[^\n]*\((\d+) themes\)", readme):
        documented_count = int(match.group(1))
        if documented_count != preset_count:
            stale_counts.append((documented_count, match.group(0)))

    assert stale_counts == [], f"README preset counts drifted from {preset_count}: {stale_counts}"


def test_readme_builtin_preset_table_matches_presets_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(r"## Built-in Presets(?P<body>.*?)(?:\n## |\Z)", readme, re.S)
    assert section, "README.md is missing the Built-in Presets section"

    documented = re.findall(r"^\| `([^`]+)` \|", section.group("body"), re.M)
    assert documented == _preset_names()


def test_live_desktop_reproducers_require_explicit_opt_in() -> None:
    source = (ROOT / "tests" / "test_bug_reproducers.py").read_text(encoding="utf-8")

    opt_in_tokens = ["LINUX_RICING_LIVE", "LINUX_RICING_ALLOW_DESKTOP_MUTATION"]
    assert any(token in source for token in opt_in_tokens), (
        "live desktop mutation tests must require an explicit environment opt-in"
    )


def test_production_text_subprocess_calls_set_utf8_encoding() -> None:
    offenders: list[str] = []
    for base in (ROOT / "scripts", ROOT / "workflow"):
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not (
                    isinstance(func, ast.Attribute)
                    and func.attr == "run"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "subprocess"
                ):
                    continue
                keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg}
                text_enabled = isinstance(keywords.get("text"), ast.Constant) and keywords["text"].value is True
                if text_enabled and "encoding" not in keywords:
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert offenders == [], "subprocess.run(text=True) calls missing encoding='utf-8': " + ", ".join(offenders)