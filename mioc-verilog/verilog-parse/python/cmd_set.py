# REV:r5
import re, shlex
import var_store as _vs
from repl_capture import capture_text as _cap

_VALID = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def register(reg):
    def _set(args, _interp=None):
        if len(args) < 3 or args[1] != '=':
            return "set: syntax error. Use: set NAME = <items...>\n"
        name = args[0]
        if not _VALID.match(name):
            return "set: invalid var name (must match [A-Za-z_][A-Za-z0-9_]*)\n"
        rhs_str = " ".join(args[2:]).strip()
        items = []
        if rhs_str.startswith("$(") and rhs_str.endswith(")"):
            inner = rhs_str[2:-1].strip()
            text = _cap(inner, _interp, reg)
            for line in text.splitlines():
                s = line.replace('\r','').strip()
                if s:
                    items.append(s)
        else:
            try:
                items = shlex.split(rhs_str, posix=True)
            except ValueError as e:
                return f"set: {e}\n"
        _vs.setv(name, items)
        return ""
    reg.add_command("set", _set, "set NAME = <items...> — define NAME as a list (quotes or $(...))")
