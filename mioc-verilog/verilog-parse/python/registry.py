
"""
registry.py — tiny command registry so each command lives in its own module.
Provides a global REG handle so command modules can auto-register at import time.
"""

from typing import Callable, Dict, List, Optional
# Avoid importing Interpreter here to prevent circular imports in some setups.
# Type hints will be minimal.

Handler = Callable[[List[str], "Interpreter"], Optional[dict]]  # type: ignore[name-defined]

class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Handler] = {}
        self._help_summary: Dict[str, str] = {}
        self._help_detail:  Dict[str, str] = {}
        self.banner_lines: List[str] = []

    def add_command(self, name: str, handler: Handler, summary: str, detail: Optional[str] = None, aliases: Optional[List[str]] = None):
        self._commands[name] = handler
        self._help_summary[name] = summary
        if detail:
            self._help_detail[name] = detail
        if aliases:
            for a in aliases:
                self._commands[a] = handler
                self._help_summary[a] = f"(alias for {name})"

    def add_banner_line(self, line: str):
        self.banner_lines.append(line)

    def list_commands(self):
        return dict(sorted(self._help_summary.items()))

    def help_detail(self, name: str) -> Optional[str]:
        return self._help_detail.get(name)

    def execute(self, line: str, interp: "Interpreter") -> Optional[dict]:  # type: ignore[name-defined]
        s = line.strip()
        if not s or s.startswith("#"):
            return None
        parts = s.split()
        cmd, args = parts[0], parts[1:]
        h = self._commands.get(cmd)
        if h is None:
            return {"__raw": f"Unknown command '{cmd}'. Type 'help' for a list of commands.\n"}
        return h(args, interp)

# ---- Global registry singleton wiring ----
REG: Optional[CommandRegistry] = None

def set_global_registry(reg: CommandRegistry):
    """Called by the launcher before importing cmd_* modules, so they can auto-register."""
    global REG
    REG = reg
