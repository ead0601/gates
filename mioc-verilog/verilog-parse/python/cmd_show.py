from typing import List
from registry import CommandRegistry
from core import Interpreter

def _handler(args: List[str], interp: Interpreter):
    if not args:
        return {"__raw": "Usage: show <target>\n"}
    if not interp.graph:
        return {"__raw": "No graph loaded. Use: read verilog <manifest.lst>\n"}
    target = args[0]
    net = interp.graph.resolve_target_to_net(target)
    if net is None:
        if "." not in target and target in interp.graph.instances:
            inst = interp.graph.instances[target]
            ctype = inst["type"]
            pins = inst.get("pins") or {}
            ins = sorted([p for p,d in interp.celllib.pin_dir_of(ctype).items() if d=="in"])
            outs= sorted([p for p,d in interp.celllib.pin_dir_of(ctype).items() if d=="out"])
            return {
                "cmd":"show",
                "target": target,
                "resolved": {"kind":"instance","id":target},
                "details": {
                    "type": ctype,
                    "pins": {"inputs": ins, "outputs": outs},
                    "connected": dict(sorted(pins.items()))
                }
            }
        return {"cmd":"show","target":target,"error":{"code":"NOT_FOUND","msg":"target not found"}}
    ninfo = interp.graph.nets.get(net, {"drivers":[],"loads":[]})
    return {
        "cmd":"show",
        "target": target,
        "resolved": {"kind":"net","id": net},
        "details": {
            "drivers": sorted(ninfo.get("drivers", []), key=lambda x:(x[0],x[1])),
            "loads":   sorted(ninfo.get("loads", []),   key=lambda x:(x[0],x[1]))
        }
    }

SUMMARY = "show <target> — inspect a net or instance"
DETAIL = """\
Usage:
  show <target>

Target can be:
  - net name (e.g., RA7, w_u23z)
  - instance name (e.g., u23)
  - instance pin (e.g., u23.z, u44.in1)
"""

def register(reg: CommandRegistry):
    reg.add_command("show", _handler, SUMMARY, DETAIL)
