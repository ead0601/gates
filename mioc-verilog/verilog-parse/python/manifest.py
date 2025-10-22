# === VNLT REV ===
# file: manifest.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:manifest
# note: r2c — shell pipeline support
# === /VNLT REV ===
from pathlib import Path
from typing import Dict, List
from builder_verilog import build_from_manifest as _build
def _parse_line(line: str):
 if ':' not in line: return None, []
 key, rest = line.split(':',1); key=key.strip()
 items=[p.strip() for p in rest.strip().split(',') if p.strip()]
 return key, items
def load_manifest(path: Path) -> Dict[str, List[str]]:
 cfg={'rtl':[],'components':[],'assigns':[],'top':[],'seq_cells':[]}
 text = path.read_text(errors='ignore')
 for raw in text.splitlines():
  s=raw.strip()
  if not s or s.startswith('#'): continue
  key, items = _parse_line(s)
  if key is None: continue
  if key not in cfg: cfg[key]=[]
  cfg[key].extend(items)
 return cfg
def load_manifest_and_build(path: Path):
 cfg = load_manifest(path)
 return _build(cfg)
