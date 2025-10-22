# === VNLT REV ===
# file: field_parser.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:fields
# note: r2c — shell pipeline support
# === /VNLT REV ===
from expander import expand_input
def _split(argstr:str):
 parts=[p.strip() for p in argstr.split(',')]
 return [p for p in parts if p!='']
def parse_fields(argstr:str, role:str='input'):
 return _split(expand_input(argstr) if role=='input' else argstr)
