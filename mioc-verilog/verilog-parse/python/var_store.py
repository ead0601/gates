# REV:r2
# Shared variable store for vnlt scripting commands
# Rule: variable values must not contain newline characters.

_VARS = {}

def _sanitize(values):
    out = []
    for v in values:
        if v is None:
            continue
        # Remove CR/LF entirely (no newlines allowed in any value)
        v = str(v).replace('\r', '').replace('\n', '')
        out.append(v)
    return out

def get(name):
    return list(_VARS.get(name, []))

def setv(name, values):
    _VARS[name] = _sanitize(values)

def unset(name):
    if name in _VARS:
        del _VARS[name]
        return True
    return False

def all_items():
    # returns list of (name, [values...]) sorted by name
    return sorted(_VARS.items(), key=lambda kv: kv[0])
