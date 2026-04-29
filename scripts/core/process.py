"""Subprocess helpers: run_cmd, cmd_exists, and KDE kwrite tool detection."""
import shutil
import subprocess


def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
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
