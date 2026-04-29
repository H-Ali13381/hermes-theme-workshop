"""Wallpaper materializer and pre-flight wallpaper snapshot helper."""
import json
import re
import subprocess
import time
from pathlib import Path

from core.constants import HOME
from core.process import run_cmd, cmd_exists
from core.backup import backup_file
from desktop_utils import discover_desktop


def _snapshot_current_wallpaper(desktop: dict) -> tuple[str | None, str | None]:
    """Return (current_wallpaper_path, method_name) or (None, None)."""
    if desktop.get("wm") == "kde" and cmd_exists("plasma-apply-wallpaperimage"):
        from core.config_parsers import _appletsrc_image
        appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        if appletsrc.exists():
            val = _appletsrc_image(appletsrc.read_text(encoding="utf-8", errors="replace"))
            if val:
                path = val[len("file://"):] if val.startswith("file://") else val
                return path, "plasma-apply-wallpaperimage"
        return None, "plasma-apply-wallpaperimage"

    if cmd_exists("awww"):
        rc, out, _ = run_cmd(["awww", "query"], timeout=5)
        if rc == 0 and out:
            for _line in out.splitlines():
                m = re.search(r"image:\s*(\S.*)$", _line)
                if m:
                    return m.group(1).strip(), "awww img"
        return None, "awww img"

    if cmd_exists("hyprpaper"):
        hyprpaper_conf = HOME / ".config" / "hypr" / "hyprpaper.conf"
        if hyprpaper_conf.exists():
            for line in hyprpaper_conf.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*wallpaper\s*=\s*[^,]*,\s*(\S+)", line)
                if m:
                    return m.group(1).strip(), "hyprpaper-config-rewrite"
        return None, "hyprpaper-config-rewrite"

    if cmd_exists("swww"):
        rc, out, _ = run_cmd(["swww", "query"], timeout=5)
        if rc == 0 and out:
            for _line in out.splitlines():
                m = re.search(r"image:\s*(\S.*)$", _line)
                if m:
                    return m.group(1).strip(), "swww img"
        return None, "swww img"

    if cmd_exists("feh"):
        fehbg = HOME / ".fehbg"
        if fehbg.exists():
            text = fehbg.read_text(encoding="utf-8", errors="replace")
            m = re.findall(r"'(/[^']+)'", text)
            if m:
                return m[-1], "feh --bg-scale"
        return None, "feh --bg-scale"

    return None, None


def materialize_wallpaper(
    design: dict,
    backup_ts: str,
    dry_run: bool = False,
) -> list[dict]:
    """Apply a wallpaper from ``design["wallpaper_path"]`` using the active setter.

    The caller must inject the resolved wallpaper path into the design dict
    under the key ``"wallpaper_path"`` before calling this function so that
    the signature matches the Materializer Contract.
    """
    wallpaper_path = design.get("wallpaper_path")
    if not wallpaper_path:
        return []

    wallpaper_path = str(Path(wallpaper_path).expanduser().resolve())
    changes = []
    desktop = discover_desktop()
    prev_wallpaper, _ = _snapshot_current_wallpaper(desktop)

    if desktop["wm"] == "kde" and cmd_exists("plasma-apply-wallpaperimage"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "plasma-apply-wallpaperimage", "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["plasma-apply-wallpaperimage", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "plasma-apply-wallpaperimage", "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("awww"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "awww img", "previous_wallpaper": prev_wallpaper})
        else:
            rc, _, _ = run_cmd(["pgrep", "awww-daemon"], timeout=3)
            if rc != 0:
                subprocess.Popen(["awww-daemon"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
                time.sleep(2)
            run_cmd(["awww", "img", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "awww img", "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("hyprpaper"):
        hyprpaper_conf = HOME / ".config" / "hypr" / "hyprpaper.conf"
        monitors = []
        if hyprpaper_conf.exists():
            for line in hyprpaper_conf.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*wallpaper\s*=\s*(\S+)\s*,", line)
                if m:
                    monitors.append(m.group(1))
        if not monitors:
            rc, out, _ = run_cmd(["hyprctl", "monitors", "-j"], timeout=5)
            if rc == 0:
                try:
                    for mon in json.loads(out):
                        monitors.append(mon.get("name", ""))
                except (json.JSONDecodeError, ValueError):
                    pass
        if not monitors:
            monitors = [""]

        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "hyprpaper-config-rewrite", "monitors": monitors,
                            "previous_wallpaper": prev_wallpaper})
            return changes

        hyprpaper_backup = backup_file(hyprpaper_conf, backup_ts, "hyprpaper/hyprpaper.conf")
        hyprpaper_conf.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"preload = {wallpaper_path}"]
        for mon in monitors:
            lines.append(f"wallpaper = {mon}, {wallpaper_path}")
        lines.append("splash = false")
        hyprpaper_conf.write_text("\n".join(lines) + "\n", encoding="utf-8")
        run_cmd(["pkill", "-x", "hyprpaper"])
        time.sleep(1)
        subprocess.Popen(["hyprpaper"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                        "method": "hyprpaper-config-rewrite", "monitors": monitors,
                        "config_path": str(hyprpaper_conf), "config_backup": hyprpaper_backup,
                        "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("swww"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "swww img", "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["swww", "img", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "swww img", "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("feh"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "feh --bg-scale", "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["feh", "--bg-scale", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "feh --bg-scale", "previous_wallpaper": prev_wallpaper})

    return changes
