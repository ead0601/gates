# === VNLT REV ===
# file: cmds/cmd_show.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:cmd
# note: r2c — shell pipeline support
# === /VNLT REV ===
from registry import CommandRegistry
def _handler(rest:str, interp)->str:
 if not interp or not interp.graph or not interp.celllib: return "No design loaded."
 g=interp.graph; lib=interp.celllib
 return (f"GatesDB summary:\n"
         f"  top_inputs={len(getattr(g,'top_inputs',[]))}\n"
         f"  top_outputs={len(getattr(g,'top_outputs',[]))}\n"
         f"  nets={len(getattr(g,'nets',{}))}\n"
         f"  instances={len(getattr(g,'instances',{}))}\n"
         f"  cell_types={len(getattr(lib,'cells',{}))}")
def register(reg: CommandRegistry): reg.register('show', _handler, 'show gates - print GatesDB summary')
