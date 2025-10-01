"""
core.py — shared data model & interpreter shell
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# ----------------------------
# Data Model
# ----------------------------

class CellLib:
    def __init__(self, data: dict):
        self.cells = data.get("cells", {})
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
        # synthetic cells
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
        self.aliases: Dict[str, dict] = netgraph.get("aliases", {})
        self.instances: Dict[str, dict] = {inst["name"]: inst for inst in netgraph.get("instances", [])}
        self.nets: Dict[str, dict] = netgraph.get("nets", {})
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

class Traversal:
    def __init__(self, graph: Graph):
        self.g = graph

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

    def _display_net(self, net: str) -> str:
        a = self.g.aliases.get(net)
        name = a.get("display") if a else net
        tags = []
        if self._is_top_in(net) or (a and a.get("kind") == "top_in"):
            tags.append("TOP_IN")
        if self._is_top_out(net):
            tags.append("TOP_OUT")
        if self._is_const(net) or (a and a.get("kind") == "const"):
            tags.append(f"CONST {net}")
        if a and a.get("invert"):
            tags.append("INV")
        return name + (" " + "".join(f"[{t}]" for t in tags) if tags else "")

    # endpoints (as in your step3)
    def collect_fanin_endpoints(self, start_net: str, *, cross_ff: bool, stage_limit: int, depth: int) -> Set[str]:
        endpoints: Set[str] = set()
        stack = [(start_net, depth, 0, tuple())]
        while stack:
            net, dleft, stages, path = stack.pop()
            if dleft < 0: continue
            if net in path: continue
            if self._is_top_in(net) or self._is_const(net):
                endpoints.add(net); continue
            for iname, opin in self._drivers_of(net):
                ctype = self.g.instances.get(iname, {}).get("type", "")
                inputs = self._inst_inputs(iname)
                if self.g.celllib.is_sequential(ctype):
                    if not cross_ff or stages >= stage_limit: continue
                    next_stages = stages + 1
                else:
                    next_stages = stages
                for ipin, inet in inputs:
                    if self._is_top_in(inet) or self._is_const(inet):
                        endpoints.add(inet); continue
                    stack.append((inet, dleft-1, next_stages, path + (net,)))
        return endpoints

    def collect_fanout_endpoints(self, start_net: str, *, depth: int) -> Set[str]:
        endpoints: Set[str] = set()
        stack = [(start_net, depth, tuple())]
        while stack:
            net, dleft, path = stack.pop()
            if dleft < 0: continue
            if net in path: continue
            if self._is_top_out(net):
                endpoints.add(net); continue
            for iname, ipin in self._loads_of(net):
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype):
                    continue
                for opin, onet in self._inst_outputs(iname):
                    if self._is_top_out(onet):
                        endpoints.add(onet); continue
                    stack.append((onet, dleft-1, path + (net,)))
        return endpoints

    def fanin_cone(self, start_net: str, depth: int = 200):
        nets_seen: Set[str] = set(); insts_seen: Set[str] = set(); edges: List[dict] = []
        stack = [(start_net, 0)]
        while stack:
            net, d = stack.pop()
            if net in nets_seen or d > depth: continue
            nets_seen.add(net)
            if net in self.g.top_inputs or net in self.g.constants: continue
            for iname, pin in self._drivers_of(net):
                insts_seen.add(iname)
                edges.append({"src": f"{iname}.{pin}", "dst": net, "kind": "data"})
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype): continue
                for ipin, inet in self._inst_inputs(iname):
                    edges.append({"src": inet, "dst": f"{iname}.{ipin}", "kind": "data"})
                    stack.append((inet, d+1))
        return nets_seen, insts_seen, self._dedupe_edges(edges)

    def fanout_cone(self, start_net: str, depth: int = 200):
        nets_seen: Set[str] = set(); insts_seen: Set[str] = set(); edges: List[dict] = []
        stack = [(start_net, 0)]
        while stack:
            net, d = stack.pop()
            if net in nets_seen or d > depth: continue
            nets_seen.add(net)
            for iname, pin in self._loads_of(net):
                insts_seen.add(iname)
                edges.append({"src": net, "dst": f"{iname}.{pin}", "kind": "data"})
                ctype = self.g.instances.get(iname, {}).get("type", "")
                if self.g.celllib.is_sequential(ctype): continue
                for opin, onet in self._inst_outputs(iname):
                    edges.append({"src": f"{iname}.{opin}", "dst": onet, "kind": "data"})
                    stack.append((onet, d+1))
        return nets_seen, insts_seen, self._dedupe_edges(edges)

    def paths_between(self, sources: List[str], sinks: List[str], depth: int = 200, max_paths: int = 200):
        sources = [s for s in sources if s in self.g.nets or s in self.g.top_inputs or s in self.g.top_outputs]
        sinks_set = set(sinks)
        out_paths: List[List[dict]] = []
        for s in sources:
            stack: List[Tuple[str, List[Tuple[str,str]]]] = [(s, [])]
            visited_on_path: Set[str] = set()
            while stack and len(out_paths) < max_paths:
                net, trail = stack.pop()
                key = f"net::{net}"
                if key in visited_on_path: continue
                visited_on_path.add(key)
                trail2 = trail + [("net", net)]
                if net in sinks_set:
                    out_paths.append(self._trail_to_nodes(trail2)); visited_on_path.remove(key); continue
                if len(trail2) // 2 > depth:
                    visited_on_path.remove(key); continue
                if net in self.g.constants:
                    visited_on_path.remove(key); continue
                loads = self._loads_of(net)
                for iname, ipin in loads:
                    ctype = self.g.instances.get(iname, {}).get("type", "")
                    pd = self.g.celllib.pin_dir_of(ctype)
                    if pd.get(ipin) != "in": continue
                    trail3 = trail2 + [("inst.pin", f"{iname}.{ipin}")]
                    if self.g.celllib.is_sequential(ctype):
                        continue
                    for opin, onet in self._inst_outputs(iname):
                        trail4 = trail3 + [("inst.pin", f"{iname}.{opin}"), ("net", onet)]
                        if onet in sinks_set:
                            out_paths.append(self._trail_to_nodes(trail4))
                            if len(out_paths) >= max_paths: break
                        else:
                            stack.append((onet, trail3 + [("inst.pin", f"{iname}.{opin}")]))
                    if len(out_paths) >= max_paths: break
                visited_on_path.remove(key)
        # dedupe
        deduped = []; seen = set()
        for p in out_paths:
            key = tuple((n["kind"], n["id"]) for n in p)
            if key not in seen: seen.add(key); deduped.append(p)
        return deduped[:max_paths]

    @staticmethod
    def _trail_to_nodes(trail: List[Tuple[str,str]]) -> List[dict]:
        return [{"kind": k, "id": i} for (k, i) in trail]

    @staticmethod
    def _dedupe_edges(edges: List[dict]) -> List[dict]:
        keys, out = set(), []
        for e in edges:
            k = (e["src"], e["dst"], e.get("kind","data"))
            if k not in keys:
                keys.add(k); out.append(e)
        out.sort(key=lambda x: (x["src"], x["dst"], x.get("kind","data")))
        return out

# ----------------------------
# Interpreter shell
# ----------------------------

class Interpreter:
    """
    Holds the live (CellLib, Graph, Traversal) and exposes load_graph()/load_celllib_graph()
    for commands like 'read verilog' to swap the active design.
    """
    def __init__(self):
        self.celllib: Optional[CellLib] = None
        self.graph:   Optional[Graph]   = None
        self.trav:    Optional[Traversal]= None
        self.graph_path: Optional[Path] = None
        self.celllib_path: Optional[Path] = None

    def load_graph(self, graph_path: Path):
        netgraph = json.loads(graph_path.read_text(errors="ignore"))
        ref = netgraph.get("celllib_ref", "celllib.json")
        celllib_path = (graph_path.parent / ref) if not Path(ref).is_absolute() else Path(ref)
        celllib = CellLib(json.loads(celllib_path.read_text(errors="ignore")))
        graph = Graph(netgraph, celllib)
        self.celllib, self.graph, self.trav = celllib, graph, Traversal(graph)
        self.graph_path, self.celllib_path = graph_path, celllib_path

    def load_celllib_graph(self, celllib_json: dict, netgraph_json: dict,
                           celllib_path: Optional[Path]=None, graph_path: Optional[Path]=None):
        celllib = CellLib(celllib_json)
        graph = Graph(netgraph_json, celllib)
        self.celllib, self.graph, self.trav = celllib, graph, Traversal(graph)
        self.celllib_path, self.graph_path = celllib_path, graph_path
