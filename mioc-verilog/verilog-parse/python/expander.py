# === VNLT REV ===
# file: expander.py
# rev:  2025-10-18 18:33  r2c  by:Drater  tag:expander
# note: r2c — shell pipeline support
# === /VNLT REV ===
import re
from expander_runtime import get_executor
import variables as VARS
def _vars_to_text(name:str)->str:
 vs=VARS.getv(name); return ','.join(vs) if vs else ''
def _apply_vars_once(s:str)->str:
 out=[]; i=0
 while i<len(s):
  if s[i]=='$':
   if i+1<len(s) and s[i+1]=='(':
    j=s.find(')',i+2)
    if j!=-1: out.append(_vars_to_text(s[i+2:j].strip())); i=j+1; continue
   m=re.match(r"\$([A-Za-z_][A-Za-z0-9_]*)", s[i:])
   if m: out.append(_vars_to_text(m.group(1))); i+=len(m.group(0)); continue
  out.append(s[i]); i+=1
 return ''.join(out)
def _find_pair(s:str,pos:int)->int:
 depth=0; i=pos; q=None; esc=False
 while i<len(s):
  ch=s[i]
  if esc: esc=False; i+=1; continue
  if ch=='\\': esc=True; i+=1; continue
  if q:
   if ch==q: q=None
   i+=1; continue
  if ch in ('\"','\''): q=ch; i+=1; continue
  if ch=='(':
   depth+=1; i+=1; continue
  if ch==')':
   depth-=1; i+=1
   if depth==0: return i
   continue
  i+=1
 return -1
def _coerce_list(t:str)->str:
 if ',' in t and '\n' not in t:
  parts=[p.strip() for p in t.split(',') if p.strip()]
 else:
  parts=[p.strip() for p in t.splitlines() if p.strip()]
 return ','.join(parts)
def _coerce_lines(t:str)->str:
 if ',' in t and '\n' not in t:
  return '\n'.join([p.strip() for p in t.split(',')])
 return '\n'.join(t.splitlines())
def _expand_inside_out(s:str)->str:
 i=0; out=[]
 while i<len(s):
  jh=s.find('#(',i); jp=s.find('%(',i)
  nxt=min([x for x in (jh,jp) if x!=-1], default=-1)
  if nxt==-1:
   out.append(_apply_vars_once(s[i:])); break
  out.append(_apply_vars_once(s[i:nxt]))
  is_hash=(nxt==jh); lpar=nxt+1; rpar=_find_pair(s,lpar)
  if rpar==-1: out.append(s[nxt:]); break
  inner_raw=s[lpar+1:rpar-1]
  inner_after=_apply_vars_once(inner_raw)
  ex=get_executor(); text=ex(inner_after.strip()) if ex else ''
  repl=_coerce_list(text) if is_hash else _coerce_lines(text)
  out.append(repl); i=rpar
 return ''.join(out)
def expand_input(s:str)->str: return _expand_inside_out(s)
def convert_output(fields:list[str])->str: return ','.join(fields)
