# === VNLT REV ===
# file: gates.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:gatesdb
# note: r2c — shell pipeline support
# === /VNLT REV ===
from dataclasses import dataclass, field
from typing import Dict, Optional, Set
@dataclass
class CellLib:
 cells: Dict[str, dict] = field(default_factory=dict)
 pin_dir: Dict[str, Dict[str,str]] = field(default_factory=dict)
 is_seq: Dict[str, bool] = field(default_factory=dict)
 def finalize(self):
  for ctype, meta in self.cells.items():
   ins=list(meta.get('inputs',[]) or []); outs=list(meta.get('outputs',[]) or [])
   pd={p:'in' for p in ins}
   for p in outs:
    if p in pd: raise ValueError(f'Pin listed as both input and output in {ctype}: {p}')
    pd[p]='out'
   self.pin_dir[ctype]=pd; self.is_seq[ctype]=(meta.get('category','comb')=='seq')
 def is_sequential(self, c): return bool(self.is_seq.get(c, False))
@dataclass
class Graph:
 top_inputs: Set[str] = field(default_factory=set)
 top_outputs: Set[str] = field(default_factory=set)
 nets: Dict[str, dict] = field(default_factory=dict)
 instances: Dict[str, dict] = field(default_factory=dict)
 aliases: Dict[str, dict] = field(default_factory=dict)
@dataclass
class Interpreter:
 celllib: Optional[CellLib] = None
 graph: Optional[Graph] = None
 def attach(self, celllib: CellLib, graph: Graph):
  self.celllib = celllib; self.graph = graph; return self
