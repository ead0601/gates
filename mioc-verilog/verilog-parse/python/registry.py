
# === VNLT REV ===
# file: registry.py
# rev:  2025-10-19 22:05  r2d  by:Drater  tag:registry
# note: provides CommandRegistry with register(), help_text(), and dispatch(line, interp)
# === /VNLT REV ===

from typing import Callable, Dict, Optional

class CommandRegistry:
    def __init__(self) -> None:
        self._cmds: Dict[str, Callable[[str, object], str]] = {}
        self._helps: Dict[str, str] = {}

    def register(self, name: str, handler: Callable[[str, object], str], helptext: Optional[str] = None) -> None:
        self._cmds[name] = handler
        if helptext:
            self._helps[name] = helptext

    def help_text(self) -> str:
        lines = ["Minimal commands:"]
        for name in sorted(self._cmds.keys()):
            ht = self._helps.get(name, "")
            if ht:
                lines.append(f"  {name:<18} {ht}")
            else:
                lines.append(f"  {name}")
        return "\n".join(lines)

    def dispatch(self, line: str, interp) -> str:
        s = (line or "").strip()
        if not s:
            return ""
        parts = s.split(None, 1)
        cmd = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        h = self._cmds.get(cmd)
        if not h:
            return f"Unknown command '{cmd}'. Type 'help' for a list of commands."
        return h(rest, interp)
