# REV:r3
# cmd_echo.py — echo with $name / ${name} expansion from var_store

import re
import var_store as _vs

_BRACED = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_SIMPLE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\b")  # word boundary to avoid $1 in awk etc.

def _expand(text: str) -> str:
    def repl_braced(m):
        name = m.group(1)
        return ' '.join(_vs.get(name))
    def repl_simple(m):
        name = m.group(1)
        return ' '.join(_vs.get(name))
    text = _BRACED.sub(repl_braced, text)
    text = _SIMPLE.sub(repl_simple, text)
    return text

def register(reg):
    def _echo(args, _interp=None):
        raw = " ".join(args)
        out = _expand(raw)
        return out + "\n"

    reg.add_command("echo", _echo, "echo <text...> — print text (with $var expansion)")
