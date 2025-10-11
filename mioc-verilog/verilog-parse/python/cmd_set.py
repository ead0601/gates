# REV:r4
# cmd_set.py — implements: set NAME = <rhs...>
# Reassembles RHS with quotes respected via shlex.split, then assigns list to NAME.
# var_store enforces: no newline characters allowed in any value.

import re
import shlex
import var_store as _vs

_VALID = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def register(reg):
    def _set(args, _interp=None):
        # Expect: NAME = items...
        if len(args) < 3 or args[1] != '=':
            return "set: syntax error. Use: set NAME = <items...>\n"
        name = args[0]
        if not _VALID.match(name):
            return "set: invalid var name (must match [A-Za-z_][A-Za-z0-9_]*)\n"
        rhs_str = " ".join(args[2:])
        try:
            items = shlex.split(rhs_str, posix=True)
        except ValueError as e:
            return f"set: {e}\n"
        _vs.setv(name, items)
        return ""

    reg.add_command("set", _set, "set NAME = <items...> — define NAME as a list (quotes respected)")
