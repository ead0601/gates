#!/usr/bin/env python3
"""
Step 3: CLI for querying a netlist graph (from Step 2).
Features:
- show <target>
- fanin  <target> [--tree] [--endpoints] [--cross-ff] [--stage-limit N] [--depth N] [--branch N]
- fanout <target> [--endpoints] [--depth N]
- paths --from A[,B...] --to X[,Y...] [--depth N] [--max-paths N]
- quit / exit

Extras:
- Persistent command history (~/.vnlt_history). On Windows: pip install pyreadline3
- Tree output always ends with a newline
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# ----------------------------
# Helpers for printing and history
# ----------------------------

def _print_raw(text: str):
    """Write text and ensure it ends with a newline."""
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.flush()

def _setup_history():
    """Enable ↑/↓ history and persist it across runs (Linux/macOS built-in; Windows needs pyreadline3)."""
    try:
        import readline  # noqa: F401
    except Exception:
        return None, False

    histfile = os.path.expanduser("~/.vnlt_history")
    try:
        if os.path.exists(histfile):
            import readline  # noqa: F401
            readline.read_history_file(histfile)
    except Exception:
        pass

    try:
        import readline  # noqa: F401
        readline.set_history_length(1000)
    except Exception:
        pass

    return histfile, True

# ----------------------------
# Data loading and helpers
# ----------------------------

class CellLib:
    def __init__(self, data: dict):
        self.cells = data.get("cells", {})
        # type -> pin->dir
        self.pin_dir: Dict[str, Dict[str, str]] = {}
        self.is_seq: Dict[str, bool] = {}
        for ctype, meta in self.cells.items():
            ins = meta.get("inputs", []) or []
            outs = meta.get("outputs", []) or []
            pd = {p: "in" for p in ins}
            for p in outs:
                if p in pd:
                    raise ValueError(f"Pin listed as both input and output in {ctype}: {p}")
                pd[p] = "out"
            self.pin_dir[ctype] = pd
            self.is_seq[ctype] = (meta.get("category", "comb") == "seq")
        # synthetic cells (buf1/inv1)
        self.pin_dir.setdefault("buf1", {"in1": "in", "z": "out"})
        self.pin_dir.setdefault("inv1", {"in1": "in", "z": "out"})
        self.is_seq.setdefault("buf1", False)
        self.is_seq.setdefault("inv1", False)

    def pin_dir_of(self, ctype: str) -> Dict[str, str]:
        return self.pin_dir.get(ctype, {})

    def is_sequential(self, ctype: str) -> bool:
        return self.is_seq.get(ctype, False)

class Graph:
    def __init__(self, netgraph: dict, celllib: CellLib):
        self.celllib = celllib
        self.top_inputs: Set[str] = set(netgraph.get("top", {}).get("inputs", []))
        self.top_outputs: Set[str] = set(netgraph.get("top", {}).get("outputs", []))
        self.constants: Set[str] = set(netgraph.get("constants", []))
        self.aliases: Dict[str, dict] = netgraph.get("aliases", {})  # e.g., PIN_IN_12 -> {"display":"BA6","invert":true,"kind":"top_in"}

        # Instances
        self.instances: Dict[str, dict] = {inst["name"]: inst for inst in netgraph.get("instances", [])}

        # Nets (drivers/loads)
        self.nets: Dict[str, dict] = netgraph.get("nets", {})

        # Quick maps: inst → outputs/inputs
        self.inst_out_nets: Dict[str, List[str]] = {}
        self.inst_in_nets: Dict[str, List[str]] = {}
        for iname, inst in self.instances.items():
            ctype = inst["type"]
            pd = self.celllib.pin_dir_of(ctype)
            outs, ins = [], []
            for pin, net in (inst.get("pins") or {}).items():
                if pd.get(pin) == "out":
                    outs.append(net)
                else:
                    ins.append(net)
            self.inst_out_nets[iname] = outs
            self.inst_in_nets[iname] = ins

    def resolve_target_to_net(self, token: str) -> Optional[str]:
        token = token.strip()
        if not token:
            return None
        if "." in token:
            iname, pin = token.split(".", 1)
            inst = self.instances.get(iname)
            if not inst:
                return None
            return (inst.get("pins") or {}).get(pin)
        if token in self.nets:
            return token
        if token in self.top_outputs or token in self.top_inputs:
            return token
        return None

# ----------------------------
# Traversal + Rendering
# ----------------------------

class Traversal:
    def __init__(self, graph: Graph):
        self.g = graph

    # --- helpers ---
    def _drivers_of(self, net: str) -> List[Tuple[str,str]]:
        return sorted(list(self.g.nets.get(net, {}).get("drivers", [])), key=lambda x: (x[0], x[1]))

    def _loads_of(self, net: str) -> List[Tuple[str,str]]:
        return sorted(list(self.g.nets.get(net, {}).get("loads", [])), key=lambda x: (x[0], x[1]))

    def _inst_inputs(self, iname: str) -> List[Tuple[str,str]]:
        inst = self.g.instances.get(iname, {})
        ctype = inst.get("type", "")
        pd = self.g.celllib.pin_dir_of(ctype)
        items = []
        for pin, net in (inst.get("pins") or {}).items():
            if pd.get(pin) == "in":
                items.append((pin, net))
        return sorted(items, key=lambda x: (x[0], x[1]))

    def _inst_outputs(self, iname: str) -> List[Tuple[str,str]]:
        inst = self.g.instances.get(iname, {})
        ctype = inst.get("type", "")
        pd = self.g.celllib.pin_dir_of(ctype)
        items = []
        for pin, net in (inst.get("pins") or {}).items():
            if pd.get(pin) == "out":
                items.append((pin, net))
        return sorted(items, key=lambda x: (x[0], x[1]))

    def _is_top_in(self, net: str) -> bool:
        if net in self.g.top_inputs:
            return True
        a = self.g.aliases.get(net)
        return bool(a and a.get("kind") == "top_in")

    def _is_top_out(self, net: str) -> bool:
        return net in self.g.top_outputs

    def _is_const(self, net: str) -> bool:
        return net in self.g.constants

    # ----- Display helpers (use aliases when present) -----
    def _display_net(self, net: str) -> str:
        a = self.g.aliases.get(net)
        name = a.get("display") if a else net
        tags: List[str] = []
        if self._is_top_in(net) or (a and a.get("kind") == "top_in"):
            tags.append("TOP_IN")
        if self._is_top_out(net):
            tags.append("TOP_OUT")
        if self._is_const(net) or (a and a.get("kind") == "const"):
            tags.append(f"CONST {net}")
        if a and a.get("invert"):
            tags.append("INV")
        return name + (" " + "".join(f"[{t}]" for t in tags) if tags else "")

    # ----- FAN-IN endpoints (TOP_IN/CONST), with optional FF crossing -----
    def collect_fanin_endpoints(self, start_net: str, *, cross_ff: bool, stage_limit: int, depth: int) -> Set[str]:
        endpoints: Set[str] = set()
        stack: List[Tuple[str,int,int,Tuple[str,...]]] = [(start_net, depth, 0, tuple())]  # net, depth_left, stages_used, path_nets

        while stack:
            net, dleft, stages, path = stack.pop()
            if dleft < 0:
                continue
            if net in path:
                continue
            # terminal?
            if self._is_top_in(net) or self._is_const(net):
                endpoints.add(net)
                continue

            # walk drivers
            for iname, opin in self._drivers_of(net):
                ctype = self.g.instances.get(iname, {}).get("type", "")
                inputs = self._inst_inputs(iname)

                # if sequential: cross only if allowed
                if self.g.celllib.is_sequential(ctype):
                    if not cross_ff or stages >= stage_limit:
                        continue
                    next_stages = stages + 1
                else:
                    next_stages = stages

                for ipin, inet in inputs:
                    if self._is_top_in(inet) or self._is_const(inet):
                        endpoints.add(inet)
                        continue
                    stack.append((inet, dleft-1, next_stages, path + (net,)))

        return endpoints

    # ----- FAN-OUT endpoints (TOP_OUT), combinational only -----
    def collect_fanout_endpoints(self, start_net: str, *, depth: int) -> Set[str]:
        endpoints: Set[str] = set()
        stack: List[Tuple[str,int,Tuple[str,...]]] = [(start_net, depth, tuple())]

        while stack:
            net, dleft, path = stack.pop()
            if dleft < 0:
                continue
            if net in path:
                continue

            if self._is_top_out(net):
                endpoints.add(net)
                continue

            for iname, ipin in self._loads_of(net):
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype):
                    continue
                for opin, onet in self._inst_outputs(iname):
                    if self._is_top_out(onet):
                        endpoints.add(onet)
                        continue
                    stack.append((onet, dleft-1, path + (net,)))

        return endpoints

    # ----- Existing JSON cone/path routines (unchanged) -----
    def fanin_cone(self, start_net: str, depth: int = 200) -> Tuple[Set[str], Set[str], List[dict]]:
        nets_seen: Set[str] = set()
        insts_seen: Set[str] = set()
        edges: List[dict] = []
        stack: List[Tuple[str,int]] = [(start_net, 0)]

        while stack:
            net, d = stack.pop()
            if net in nets_seen or d > depth:
                continue
            nets_seen.add(net)

            if net in self.g.top_inputs or net in self.g.constants:
                continue

            for iname, pin in self._drivers_of(net):
                insts_seen.add(iname)
                edges.append({"src": f"{iname}.{pin}", "dst": net, "kind": "data"})
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype):
                    continue
                for ipin, inet in self._inst_inputs(iname):
                    edges.append({"src": inet, "dst": f"{iname}.{ipin}", "kind": "data"})
                    stack.append((inet, d+1))

        return nets_seen, insts_seen, self._dedupe_edges(edges)

    def fanout_cone(self, start_net: str, depth: int = 200) -> Tuple[Set[str], Set[str], List[dict]]:
        nets_seen: Set[str] = set()
        insts_seen: Set[str] = set()
        edges: List[dict] = []
        stack: List[Tuple[str,int]] = [(start_net, 0)]

        while stack:
            net, d = stack.pop()
            if net in nets_seen or d > depth:
                continue
            nets_seen.add(net)

            for iname, pin in self._loads_of(net):
                insts_seen.add(iname)
                edges.append({"src": net, "dst": f"{iname}.{pin}", "kind": "data"})
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype):
                    continue
                for opin, onet in self._inst_outputs(iname):
                    edges.append({"src": f"{iname}.{opin}", "dst": onet, "kind": "data"})
                    stack.append((onet, d+1))

        return nets_seen, insts_seen, self._dedupe_edges(edges)

    def paths_between(self, sources: List[str], sinks: List[str],
                      depth: int = 200, max_paths: int = 200) -> List[List[dict]]:
        sources = [s for s in sources if s in self.g.nets or s in self.g.top_inputs or s in self.g.top_outputs]
        sinks_set = set(sinks)
        out_paths: List[List[dict]] = []

        for s in sources:
            stack: List[Tuple[str, List[Tuple[str,str]]]] = [(s, [])]
            visited_on_path: Set[str] = set()

            while stack and len(out_paths) < max_paths:
                net, trail = stack.pop()
                key = f"net::{net}"
                if key in visited_on_path:
                    continue
                visited_on_path.add(key)

                trail2 = trail + [("net", net)]
                if net in sinks_set:
                    out_paths.append(self._trail_to_nodes(trail2))
                    visited_on_path.remove(key)
                    continue
                if len(trail2) // 2 > depth:
                    visited_on_path.remove(key)
                    continue
                if net in self.g.constants:
                    visited_on_path.remove(key)
                    continue

                loads = self._loads_of(net)
                for iname, ipin in loads:
                    ctype = self.g.instances.get(iname, {}).get("type", "")
                    pd = self.g.celllib.pin_dir_of(ctype)
                    if pd.get(ipin) != "in":
                        continue
                    trail3 = trail2 + [("inst.pin", f"{iname}.{ipin}")]
                    if self.g.celllib.is_sequential(ctype):
                        continue
                    for opin, onet in self._inst_outputs(iname):
                        trail4 = trail3 + [("inst.pin", f"{iname}.{opin}"), ("net", onet)]
                        if onet in sinks_set:
                            out_paths.append(self._trail_to_nodes(trail4))
                            if len(out_paths) >= max_paths:
                                break
                        else:
                            stack.append((onet, trail3 + [("inst.pin", f"{iname}.{opin}")]))
                    if len(out_paths) >= max_paths:
                        break

                visited_on_path.remove(key)

        deduped = []
        seen = set()
        for p in out_paths:
            key = tuple((n["kind"], n["id"]) for n in p)
            if key not in seen:
                seen.add(key)
                deduped.append(p)
        return deduped[:max_paths]

    # ---------- FAN-IN TREE (alias display + leaf-echo suppression) ----------
    def render_fanin_tree(self, start_net: str, *, cross_ff: bool=False, stage_limit: int=0,
                          depth: int=200, branch_limit: Optional[int]=None) -> str:
        lines: List[str] = []
        lines.append(f"{self._display_net(start_net)}")

        seen_node_idx: Dict[str, int] = {}
        node_counter = [1]

        def add_line(prefix: str, is_last: bool, text: str):
            branch = "└─ " if is_last else "├─ "
            lines.append(prefix + branch + text)

        def child_prefix(prefix: str, is_last: bool) -> str:
            return prefix + ("   " if is_last else "│  ")

        def dfs_net(net: str, prefix: str, depth_left: int, stages_used: int,
                    path_seen_nets: Set[str]):
            if depth_left < 0:
                add_line(prefix, True, "(depth limit)")
                return
            if net in path_seen_nets:
                add_line(prefix, True, f"(loop) {self._display_net(net)}")
                return
            # terminals: show only once (on parent pin line), don't echo here
            if self._is_top_in(net) or self._is_const(net):
                return

            path_seen_nets.add(net)
            drivers = self._drivers_of(net)
            if not drivers:
                add_line(prefix, True, f"{self._display_net(net)} [undriven?]")
                path_seen_nets.remove(net)
                return

            for i, (iname, opin) in enumerate(drivers):
                is_last_drv = (i == len(drivers)-1)
                inst = self.g.instances.get(iname, {})
                ctype = inst.get("type", "")
                node_id = f"{iname}.{opin}"
                if node_id in seen_node_idx:
                    add_line(prefix, is_last_drv, f"↪ see ▲{seen_node_idx[node_id]} {node_id}")
                    continue
                seen_node_idx[node_id] = node_counter[0]
                node_counter[0] += 1

                add_line(prefix, is_last_drv, f"{iname}.{opin} ({ctype})" + (" [FF]" if self.g.celllib.is_sequential(ctype) else ""))

                inputs = self._inst_inputs(iname)
                crossing = self.g.celllib.is_sequential(ctype)
                may_cross = crossing and cross_ff and stages_used < stage_limit
                if crossing and not may_cross:
                    if inputs:
                        p2 = child_prefix(prefix, is_last_drv)
                        add_line(p2, True, "(stop at FF)")
                    continue

                shown = inputs
                more = 0
                if branch_limit is not None and len(inputs) > branch_limit:
                    shown = inputs[:branch_limit]
                    more = len(inputs) - branch_limit

                for j, (ipin, inet) in enumerate(shown):
                    is_last_in = (j == len(shown)-1) and (more == 0)
                    p2 = child_prefix(prefix, is_last_drv)
                    crossed_note = " [crossed FF]" if crossing else ""
                    pin_text = f"{ipin} ← {self._display_net(inet)}{crossed_note}"
                    add_line(p2, is_last_in if more == 0 else False, pin_text)
                    # if terminal (TOP_IN/CONST), don't echo leaf
                    if self._is_top_in(inet) or self._is_const(inet):
                        continue
                    p3 = child_prefix(p2, is_last_in and more == 0)
                    dfs_net(inet, p3, depth_left-1, stages_used + (1 if crossing else 0), path_seen_nets)

                if more > 0:
                    p2 = child_prefix(prefix, is_last_drv)
                    add_line(p2, True, f"(+{more} more…)")

            path_seen_nets.remove(net)

        dfs_net(start_net, "", depth, 0, set())
        return "\n".join(lines)

    # ----- utils -----
    @staticmethod
    def _trail_to_nodes(trail: List[Tuple[str,str]]) -> List[dict]:
        return [{"kind": k, "id": i} for (k, i) in trail]

    @staticmethod
    def _dedupe_edges(edges: List[dict]) -> List[dict]:
        keys = set()
        out = []
        for e in edges:
            k = (e["src"], e["dst"], e.get("kind","data"))
            if k not in keys:
                keys.add(k)
                out.append(e)
        out.sort(key=lambda x: (x["src"], x["dst"], x.get("kind","data")))
        return out

# ----------------------------
# Interpreter (commands → output)
# ----------------------------

class Interpreter:
    def __init__(self, graph_path: Path):
        self.graph_path = graph_path
        self.netgraph = json.loads(graph_path.read_text(errors="ignore"))
        ref = self.netgraph.get("celllib_ref", "celllib.json")
        celllib_path = (graph_path.parent / ref) if not Path(ref).is_absolute() else Path(ref)
        self.celllib = CellLib(json.loads(celllib_path.read_text(errors="ignore")))
        self.graph = Graph(self.netgraph, self.celllib)
        self.trav = Traversal(self.graph)

    def _resolve(self, token: str) -> Optional[str]:
        return self.graph.resolve_target_to_net(token)

    def cmd_show(self, args: List[str]) -> dict:
        if not args:
            return {"cmd":"show","error":{"code":"USAGE","msg":"show <target>"}}
        target = args[0]
        net = self._resolve(target)
        if net is None:
            if "." not in target and target in self.graph.instances:
                inst = self.graph.instances[target]
                ctype = inst["type"]
                pins = inst.get("pins") or {}
                ins = sorted([p for p,d in self.celllib.pin_dir_of(ctype).items() if d=="in"])
                outs= sorted([p for p,d in self.celllib.pin_dir_of(ctype).items() if d=="out"])
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
        ninfo = self.graph.nets.get(net, {"drivers":[],"loads":[]})
        return {
            "cmd":"show",
            "target": target,
            "resolved": {"kind":"net","id": net},
            "details": {
                "drivers": sorted(ninfo.get("drivers", []), key=lambda x:(x[0],x[1])),
                "loads":   sorted(ninfo.get("loads", []),   key=lambda x:(x[0],x[1]))
            }
        }

    def _print_endpoints(self, header: str, nets: Set[str]) -> dict:
        if not nets:
            return {"__raw": f"{header}\n  (none)\n"}
        lines = [header]
        for n in sorted(nets):
            lines.append(f"  - {self.trav._display_net(n)}")
        return {"__raw": "\n".join(lines) + "\n"}

    def cmd_fanin(self, args: List[str]):
        if not args:
            return {"cmd":"fanin","error":{"code":"USAGE","msg":"fanin <target> [--tree|--endpoints] [--depth N] [--cross-ff] [--stage-limit N] [--branch N]"}}
        tree_mode = False
        endpoints_mode = False
        cross_ff = False
        stage_limit = 0
        depth = 200
        branch_limit: Optional[int] = None
        tokens: List[str] = []
        it = iter(args)
        for a in it:
            if a == "--tree":
                tree_mode = True
            elif a == "--endpoints":
                endpoints_mode = True
            elif a == "--cross-ff":
                cross_ff = True
                if stage_limit == 0:
                    stage_limit = 999999
            elif a == "--stage-limit":
                try:
                    stage_limit = int(next(it))
                except Exception:
                    return {"cmd":"fanin","error":{"code":"USAGE","msg":"--stage-limit N"}}
            elif a == "--depth":
                try:
                    depth = int(next(it))
                except Exception:
                    return {"cmd":"fanin","error":{"code":"USAGE","msg":"--depth N"}}
            elif a == "--branch":
                try:
                    branch_limit = int(next(it))
                except Exception:
                    return {"cmd":"fanin","error":{"code":"USAGE","msg":"--branch N"}}
            else:
                tokens.append(a)

        target = tokens[0] if tokens else ""
        net = self._resolve(target)
        if net is None:
            return {"cmd":"fanin","target":target,"error":{"code":"NOT_FOUND","msg":"target not found"}}

        if endpoints_mode:
            eps = self.trav.collect_fanin_endpoints(net, cross_ff=cross_ff,
                                                    stage_limit=(stage_limit if cross_ff else 0),
                                                    depth=depth)
            return self._print_endpoints(f"FANIN ENDPOINTS (TOP_IN/CONST) for {target}", eps)

        if tree_mode:
            text = self.trav.render_fanin_tree(net, cross_ff=cross_ff,
                                               stage_limit=stage_limit if cross_ff else 0,
                                               depth=depth, branch_limit=branch_limit)
            return {"__raw": text}

        # default: cone JSON
        nets, insts, edges = self.trav.fanin_cone(net, depth=depth)
        return {
            "cmd":"fanin","target":target,"mode":"cone",
            "nodes":{"nets":sorted(nets),"instances":sorted(insts)},
            "edges":edges,
            "meta":{"direction":"in","depth":depth,"stop":["ff","io","const"]}
        }

    def cmd_fanout(self, args: List[str]) -> dict:
        if not args:
            return {"cmd":"fanout","error":{"code":"USAGE","msg":"fanout <target> [--endpoints] [--depth N]"}}
        endpoints_mode = False
        depth = 200
        tokens: List[str] = []
        it = iter(args)
        for a in it:
            if a == "--endpoints":
                endpoints_mode = True
            elif a == "--depth":
                try:
                    depth = int(next(it))
                except Exception:
                    return {"cmd":"fanout","error":{"code":"USAGE","msg":"--depth N"}}
            else:
                tokens.append(a)
        target = tokens[0] if tokens else ""
        net = self._resolve(target)
        if net is None:
            return {"cmd":"fanout","target":target,"error":{"code":"NOT_FOUND","msg":"target not found"}}

        if endpoints_mode:
            eps = self.trav.collect_fanout_endpoints(net, depth=depth)
            return self._print_endpoints(f"FANOUT ENDPOINTS (TOP_OUT) for {target}", eps)

        nets, insts, edges = self.trav.fanout_cone(net, depth=depth)
        return {
            "cmd":"fanout","target":target,"mode":"cone",
            "nodes":{"nets":sorted(nets),"instances":sorted(insts)},
            "edges":edges,
            "meta":{"direction":"out","depth":depth,"stop":["ff"]}
        }

    def cmd_paths(self, args: List[str]) -> dict:
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
                return {"cmd":"paths","error":{"code":"USAGE","msg":"paths --from A[,B] --to X[,Y] [--depth N] [--max-paths N]"}}

        if not froms or not tos:
            return {"cmd":"paths","error":{"code":"USAGE","msg":"paths --from A[,B] --to X[,Y]"}}

        src_nets, sink_nets = [], []
        for f in froms:
            n = self._resolve(f)
            if n is None:
                return {"cmd":"paths","error":{"code":"NOT_FOUND","msg":f"source not found: {f}"}}
            src_nets.append(n)
        for t in tos:
            n = self._resolve(t)
            if n is None:
                return {"cmd":"paths","error":{"code":"NOT_FOUND","msg":f"sink not found: {t}"}}
            sink_nets.append(n)

        paths = self.trav.paths_between(src_nets, sink_nets, depth=depth, max_paths=max_paths)
        return {"cmd":"paths","from": froms, "to": tos, "paths": paths, "meta": {"depth": depth, "max_paths": max_paths, "stop":["ff"]}}

    def execute(self, line: str) -> Optional[dict]:
        s = line.strip()
        if not s or s.startswith("#"):
            return None
        parts = s.split()
        if not parts:
            return None
        cmd, args = parts[0], parts[1:]
        if cmd == "show":
            return self.cmd_show(args)
        if cmd == "fanin":
            return self.cmd_fanin(args)
        if cmd == "fanout":
            return self.cmd_fanout(args)
        if cmd == "paths":
            return self.cmd_paths(args)
        if cmd in ("quit","exit"):
            return {"cmd":"quit"}
        return {"cmd":cmd,"error":{"code":"UNKNOWN_CMD","msg":"unknown command"}}

# ----------------------------
# REPL / Batch
# ----------------------------

def run_repl(interp: Interpreter):
    histfile, hist_ok = _setup_history()
    try:
        while True:
            try:
                line = input("vnlt> ")
            except EOFError:
                break
            res = interp.execute(line)
            if res is None:
                continue
            if res.get("cmd") == "quit":
                break
            if "__raw" in res:
                _print_raw(res["__raw"])
            else:
                print(json.dumps(res, sort_keys=False))
    except KeyboardInterrupt:
        pass
    finally:
        if hist_ok and histfile:
            try:
                import readline  # noqa: F401
                readline.write_history_file(histfile)
            except Exception:
                pass

def run_batch(interp: Interpreter, script_path: Path):
    for raw in script_path.read_text(errors="ignore").splitlines():
        res = interp.execute(raw)
        if res is None:
            continue
        if res.get("cmd") == "quit":
            break
        if "__raw" in res:
            _print_raw(res["__raw"])
        else:
            print(json.dumps(res, sort_keys=False))

def main():
    ap = argparse.ArgumentParser(description="Step 3: CLI for netgraph.json (tree + endpoints).")
    ap.add_argument("--graph", required=True, help="Path to netgraph.json from Step 2")
    ap.add_argument("-y", "--batch", help="Run commands from a file (blank lines and # comments ignored)")
    args = ap.parse_args()

    interp = Interpreter(Path(args.graph))
    if args.batch:
        run_batch(interp, Path(args.batch))
    else:
        run_repl(interp)

if __name__ == "__main__":
    main()
