# === VNLT REV ===
# file: python/cmd_paths.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

from typing import List
from registry import CommandRegistry
from core import Interpreter
import fnmatch

SUMMARY = "paths --from A[,B] --to X[,Y] [--depth N] [--max-paths N]"
DETAIL = """\
Usage:
  paths --from A[,B,...] --to X[,Y,...] [--depth N] [--max-paths N]

Description:
  Find combinational paths from sources to sinks (no FF crossing).
  You can pass nets, ports, or pins; pins/ports are resolved to nets automatically.
  Wildcards (* ? [..]) are allowed on --to targets; --from must be explicit.
Examples:
  paths --from PORT:IN0 --to PORT:OUT* --depth 100 --max-paths 50
  paths --from u12.z   --to mioc_flop*.D
"""

def _has_glob(s: str) -> bool:
    return any(c in s for c in "*?[")

def _resolve_one(token: str, interp: Interpreter) -> str:
    """Resolve a token (INST.PIN / PORT:NAME / NET:NAME / bare net) to a net name."""
    net = interp.graph.resolve_target_to_net(token)
    return net if net is not None else token

def _expand_to_targets(patterns: List[str], interp: Interpreter) -> List[str]:
    """Expand --to patterns (allowing globs) into concrete net names."""
    g = interp.graph
    out: List[str] = []
    for pat in patterns:
        if _has_glob(pat):
            # Match against ports and nets
            # Ports
            for p in sorted(set(g.top_inputs) | set(g.top_outputs)):
                if fnmatch.fnmatch(p, pat):
                    net = _resolve_one(f"PORT:{p}", interp)
                    if net:
                        out.append(net)
            # Nets
            for n in g.nets.keys():
                if fnmatch.fnmatch(n, pat):
                    out.append(n)
        else:
            out.append(_resolve_one(pat, interp))
    # Deduplicate, keep order
    seen = set(); deduped = []
    for t in out:
        if t not in seen:
            seen.add(t); deduped.append(t)
    return deduped

def _format_paths(paths: List[List[dict]]) -> str:
    lines = []
    for i, path in enumerate(paths, 1):
        segs = [node["id"] for node in path]
        lines.append(f"[{i}] " + " → ".join(segs))
    if not lines:
        lines.append("0 paths")
    return "\n".join(lines) + "\n"

def _handler(args: List[str], interp: Interpreter):
    if not interp.trav:
        return {"__raw": "No graph loaded. Use: read verilog <manifest.lst>\n"}

    froms: List[str] = []
    tos: List[str] = []
    depth = 200
    max_paths = 200

    it = iter(args)
    for a in it:
        if a == "--from":
            froms = [s.strip() for s in next(it).split(",")]
        elif a == "--to":
            tos = [s.strip() for s in next(it).split(",")]
        elif a == "--depth":
            depth = int(next(it))
        elif a == "--max-paths":
            max_paths = int(next(it))
        else:
            return {"__raw": DETAIL}

    if not froms or not tos:
        return {"__raw": DETAIL}

    # Resolve --from explicitly (no globs)
    src_nets = [_resolve_one(tok, interp) for tok in froms]
    # Expand/resolve --to (globs allowed)
    dst_nets = _expand_to_targets(tos, interp)

    # Keep only nets/ports that actually exist in the graph universe
    g = interp.graph
    src_nets = [s for s in src_nets if s in g.nets or s in g.top_inputs or s in g.top_outputs]
    dst_nets = [t for t in dst_nets if t in g.nets or t in g.top_inputs or t in g.top_outputs]

    if not src_nets or not dst_nets:
        return {"__raw": "paths: no valid sources or sinks after resolution\n"}

    paths = interp.trav.paths_between(src_nets, dst_nets, depth=depth, max_paths=max_paths)
    return {
        "__raw": _format_paths(paths),
        "from": src_nets,
        "to": dst_nets,
        "paths": paths,
        "meta": {"depth": depth, "max_paths": max_paths, "stop": ["ff"]}
    }

def register(reg: CommandRegistry):
    # also register a short alias 'path'
    reg.add_command("paths", _handler, SUMMARY, DETAIL, aliases=["path"])
