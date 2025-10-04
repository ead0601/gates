# === VNLT REV ===
# file: python/cmd_help.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

# Centralized help command wired to your registry's add_command() and global REG.

from typing import List, Optional
import registry

SUMMARY = "help [<command>] — list commands or show detailed help for one command"
DETAIL = """
Usage:
  help
      Show all available commands with a one-line summary.

  help <command>
      Show detailed help for the given command, if available.
""".strip()


def _print_all(reg: registry.CommandRegistry):
    items = reg.list_commands()  # name -> summary (sorted by name in your impl)
    if not items:
        print("No commands are registered.")
        return
    print("Available commands:")
    width = max(len(name) for name in items) if items else 0
    for name, summary in items.items():
        print(f"  {name.ljust(width)}  {summary}")


def _print_one(reg: registry.CommandRegistry, name: str):
    detail = reg.help_detail(name)
    if detail:
        print(detail)
        return
    items = reg.list_commands()
    if name in items:
        # fallback to the one-line summary
        print(f"{name} — {items[name]}")
        return
    print(f"Unknown command '{name}'. Type 'help' to see the list.")


# ********** handler signature must be (argv, interp) **********
def run(argv: List[str], interp) -> Optional[dict]:
    if not argv:
        _print_all(registry.REG)  # type: ignore[arg-type]
        return None
    _print_one(registry.REG, argv[0])  # type: ignore[arg-type]
    return None


def help() -> str:
    return DETAIL


def register(reg: registry.CommandRegistry):
    # Your registry API:
    #   add_command(name, handler, summary, detail=None, aliases=None)
    reg.add_command("help", run, SUMMARY, DETAIL, aliases=None)
