# === VNLT REV ===
# file: variables.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:vars
# note: r2c — shell pipeline support
# === /VNLT REV ===
_STORE={}
def _sanitize(vs):
 out=[]
 for v in vs:
  if v is None: continue
  out.append(str(v).replace('\n','').replace('\r',''))
 return out
def setv(n,vs): _STORE[str(n)]=_sanitize(vs)
def getv(n): return list(_STORE.get(str(n),[]))
def unset(n): return _STORE.pop(str(n),None) is not None
def all_items(): return sorted(_STORE.items(), key=lambda kv: kv[0])
