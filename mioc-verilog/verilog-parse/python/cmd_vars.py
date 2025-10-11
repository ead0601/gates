# REV:r6
# cmd_vars.py — implements: vars [NAME]

import var_store as _vs

def register(reg):
    def _vars(args, _interp=None):
        if not args:
            items = _vs.all_items()
            if not items:
                return "(no vars)"
            chunks = []
            for k, vals in items:
                chunks.append(f"{k} = {' '.join(vals)}")
            return ", ".join(chunks)
        # vars NAME -> single line, numbered entries separated by ", "
        name = args[0]
        vals = _vs.get(name)
        if not vals:
            return "(undefined)"
        parts = [f"{i+1}: {v}" for i, v in enumerate(vals)]
        return ", ".join(parts)

    reg.add_command("vars", _vars, "vars [NAME] — list all variables or show items for NAME")
