# === VNLT REV ===
# file: cmds/cmd_save_db.py
# rev:  2025-10-19 05:31  r2  by:Drater  tag:cmd
# note: JSON-safe dump; recursively converts set→sorted list (and nested containers) before writing
# === /VNLT REV ===

from registry import CommandRegistry
from typing import Any, Dict
import os, json, pathlib

def _repo_root_from_this_file() -> str:
    here = pathlib.Path(__file__).resolve()
    return str(here.parents[2])  # .../python/cmds -> .../python -> repo root

def _to_json_safe(obj: Any):
    try:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, (set, frozenset)):
            return sorted([_to_json_safe(v) for v in obj], key=lambda x: str(x))
        if isinstance(obj, dict):
            return {str(k): _to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_json_safe(v) for v in obj]
        if hasattr(obj, "__dict__"):
            return _to_json_safe(vars(obj))
        return str(obj)
    except Exception:
        return str(obj)

def _serialize_celllib(celllib: Any) -> Dict:
    if celllib is None:
        return {}
    if isinstance(celllib, dict):
        return celllib
    out = {}
    for key in ["pin_dirs", "is_seq", "types", "cells", "name", "version"]:
        if hasattr(celllib, key):
            out[key] = getattr(celllib, key)
    if not out:
        tmp = {}
        for k in dir(celllib):
            if k.startswith("_"):
                continue
            try:
                v = getattr(celllib, k)
            except Exception:
                continue
            if callable(v):
                continue
            tmp[k] = v
        out = tmp
    return out

def _serialize_graph(graph: Any) -> Dict:
    if graph is None:
        return {}
    if isinstance(graph, dict):
        return graph
    keys = ["top_inputs","top_outputs","constants","aliases","instances","nets","name","rev"]
    out = {}
    for k in keys:
        if hasattr(graph, k):
            out[k] = getattr(graph, k)
    if not out:
        tmp = {}
        for k in dir(graph):
            if k.startswith("_"):
                continue
            try:
                v = getattr(graph, k)
            except Exception:
                continue
            if callable(v):
                continue
            tmp[k] = v
        out = tmp
    return out

def _handler(rest: str, interp) -> str:
    if not interp or not getattr(interp, "graph", None):
        return "No design loaded."
    root = _repo_root_from_this_file()
    vol_dir = os.path.join(root, "volatile")
    os.makedirs(vol_dir, exist_ok=True)

    celllib_dict = _serialize_celllib(getattr(interp, "celllib", None))
    graph_dict   = _serialize_graph(getattr(interp, "graph", None))

    try:
        if isinstance(graph_dict, dict):
            graph_dict.setdefault("celllib_ref", "celllib.json")
    except Exception:
        pass

    celllib_path = os.path.abspath(os.path.join(vol_dir, "celllib.json"))
    graph_path   = os.path.abspath(os.path.join(vol_dir, "graph.json"))

    celllib_safe = _to_json_safe(celllib_dict)
    graph_safe   = _to_json_safe(graph_dict)

    with open(celllib_path, "w", encoding="utf-8") as f:
        import json
        json.dump(celllib_safe, f, indent=2, sort_keys=True)
    with open(graph_path, "w", encoding="utf-8") as f:
        import json
        json.dump(graph_safe, f, indent=2, sort_keys=True)

    return f"Saved:\n  {celllib_path}\n  {graph_path}"

def register(reg: CommandRegistry):
    reg.register("save_db", _handler, "save_db — write celllib.json and graph.json to ../volatile/")
