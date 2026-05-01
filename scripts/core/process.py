"""Subprocess helpers: run_cmd, cmd_exists, KDE kwrite tool detection,
and live-state snapshot readers (gsettings_get, _kread, _hyprctl_getoption_gradient)
used by materializers to capture pre-apply values for undo/rollback."""
import re
import shutil
import subprocess


def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (OSError, subprocess.SubprocessError, TimeoutError) as e:
        return -1, "", str(e)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _get_kwrite() -> str | None:
    if cmd_exists("kwriteconfig6"):
        return "kwriteconfig6"
    if cmd_exists("kwriteconfig5"):
        return "kwriteconfig5"
    return None


def gsettings_get(schema: str, key: str) -> str | None:
    """Read one gsettings key; return the raw GVariant output string or None.

    The value is returned in GVariant format as ``gsettings get`` prints it
    (e.g. ``'Adwaita-dark'`` for a string).  This can be passed directly as
    the VALUE argument to ``gsettings set``, which also accepts GVariant syntax,
    making round-trip snapshot/restore straightforward.

    Returns None when ``gsettings`` is not installed or the key is unset.
    """
    if not cmd_exists("gsettings"):
        return None
    rc, out, _ = run_cmd(["gsettings", "get", schema, key])
    if rc == 0 and out:
        return out
    return None


def _kread(file: str, group: str, key: str) -> str | None:
    """Read one key from a KDE config file via kreadconfig6 or kreadconfig5.

    Tries kreadconfig6 first; falls back to kreadconfig5 if the tool is absent
    or the key is not set.  Returns the value string or None.
    """
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", file, "--group", group, "--key", key])
            if rc == 0 and out:
                return out
    return None


def _hyprctl_getoption_gradient(option: str) -> str | None:
    """Return the current live value of a Hyprland gradient option, or None.

    Runs ``hyprctl getoption <option>`` and parses the ``gradient = …`` line.
    Returns the raw gradient string (e.g. ``rgba(aabbccee) rgba(aabbccee) 45deg``)
    or ``None`` if hyprctl is unavailable, the option is unset, or parsing fails.
    """
    rc, out, _ = run_cmd(["hyprctl", "getoption", option], timeout=5)
    if rc != 0 or not out:
        return None
    m = re.search(r"^\s+gradient\s*=\s*(.+)$", out, re.MULTILINE)
    if m:
        val = m.group(1).strip()
        return val if val else None
    return None
