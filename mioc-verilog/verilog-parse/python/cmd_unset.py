# REV:r3
# cmd_unset.py — implements: unset NAME

import var_store as _vs
import re

_VALID = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def register(reg):
    def _unset(args, _interp=None):
        if len(args) != 1 or not _VALID.match(args[0]):
            return "unset: usage: unset NAME\n"
        ok = _vs.unset(args[0])
        if not ok:
            return "(undefined)\n"
        return ""

    reg.add_command("unset", _unset, "unset NAME — remove variable NAME")
