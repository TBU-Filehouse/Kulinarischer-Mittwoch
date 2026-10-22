"""PreToolUse hook: stop agent loops without progress and foreground commands that never end.

Reads the Claude Code hook event as JSON from stdin. Exit 2 blocks the tool call and
shows the reason to the agent; exit 0 allows it. State lives in the temp directory,
never in the repository. KUMI_LOOP_GUARD=off disables the guard (emergency stop).
Any internal error fails open, so a broken guard cannot block normal work.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

_HISTORY = 6
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_BOUNDED = re.compile(r"\s*timeout\s+\d+[smh]?\s+[^;&|]*$")
_HANGS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"-m\s+(app|http\.server)\b",
    r"\bflask\s+run\b",
    r"\btail\s+(-\S+\s+)*-[a-z]*f",
    r"\bget-content\b.*\s-wait\b",
    r"\bping\b.*\s-t\b",
    r"\bwhile\s+(true\b|:|\(\s*\$true\s*\))",
))


def _hang_reason(tool_input: dict) -> str | None:
    command = tool_input.get("command")
    if not isinstance(command, str) or tool_input.get("run_in_background"):
        return None
    unquoted = _QUOTED.sub("", command)
    if _BOUNDED.match(unquoted):  # `timeout N …` ends on its own.
        return None
    if any(pattern.search(unquoted) for pattern in _HANGS):
        return ("Loop-Guard: Dieser Befehl endet im Vordergrund nicht (Server, Endlosschleife oder "
                "Dauerausgabe). Im Hintergrund starten (run_in_background) oder einen Befehl mit Ende wählen.")
    return None


def _fingerprint(tool_name: str, tool_input: dict) -> str:
    relevant = {key: value for key, value in tool_input.items() if key != "description"}
    payload = json.dumps([tool_name, relevant], sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_loop(recent: list[str]) -> bool:
    if len(recent) >= 3 and len(set(recent[-3:])) == 1:
        return True
    last = recent[-6:]
    return len(last) == 6 and last[0] != last[1] and last == [last[0], last[1]] * 3


def evaluate(event: dict, state_dir: str | Path) -> tuple[int, str]:
    """Return (exit_code, message) for one hook event."""
    if os.environ.get("KUMI_LOOP_GUARD", "").lower() == "off":
        return 0, ""
    try:
        tool_name = event.get("tool_name")
        tool_input = event.get("tool_input")
        if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
            return 0, ""
        reason = _hang_reason(tool_input)
        if reason:
            return 2, reason
        session = re.sub(r"[^A-Za-z0-9_-]", "_", str(event.get("session_id") or "unknown"))[:80]
        state_path = Path(state_dir) / f"{session}.json"
        try:
            recent = json.loads(state_path.read_text(encoding="utf-8"))["recent"]
            if not isinstance(recent, list):
                recent = []
        except (OSError, ValueError, KeyError, TypeError):
            recent = []
        recent = (recent + [_fingerprint(tool_name, tool_input)])[-_HISTORY:]
        blocked = _is_loop(recent)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"recent": [] if blocked else recent}), encoding="utf-8")
        if blocked:
            return 2, ("Loop-Guard: Schleife ohne Fortschritt erkannt (gleicher Aufruf wiederholt). "
                       "Ursache prüfen, Ansatz ändern oder die Person fragen statt erneut zu versuchen.")
        return 0, ""
    except Exception:  # noqa: BLE001 - a guard must never break the session.
        return 0, ""


def main() -> int:
    state_dir = os.environ.get("KUMI_LOOP_GUARD_DIR") or Path(tempfile.gettempdir()) / "kumi-loop-guard"
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except ValueError:
        return 0
    code, message = evaluate(event if isinstance(event, dict) else {}, state_dir)
    if message:
        # Windows consoles default to ANSI; hook readers expect UTF-8.
        sys.stderr.buffer.write((message + "\n").encode("utf-8"))
        sys.stderr.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
