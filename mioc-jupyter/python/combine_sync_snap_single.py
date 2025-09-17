#!/usr/bin/env python3
# combine_sync_snap_single_r3p3.py
# Revision: r3p3 (2025-09-16)
#
# Purpose
#   Combine LA1/LA2/LA3 VCDs, align their D1 clocks, and retime selected signals to the D1 edge grid
#   using “snap-back” DDR policy:
#     - At each cycle k:
#         • sample at HIGH midpoint -> snap that value back to posedge R_k
#         • sample at LOW  midpoint -> snap that value back to negedge F_k
#   Output one rail per pin name (no _POS/_NEG), updating only at D1 edges.
#
# Scopes written:
#   SYNC → LA1/LA2/LA3 → SYNC
#   INPUTS / OUTPUTS / IO / (OPTIONAL OTHER) → LA1/LA2/LA3 → <alias>
#
# Usage (includes INPUTS, OUTPUTS, IO by default):
#   python3 combine_sync_snap_single_r3p3.py \
#     -d ./la1010 \
#     -c ./LA1010_config.txt \
#     --sync D1 \
#     -o SYNC_ALIGNED.vcd
#
# To limit roles:
#   --roles INPUTS
#   --roles INPUTS,OUTPUTS
#
# Notes
#   - Aliases are read from LA1010_config.txt lines like:
#       IN , LA1:D00, A0                  # comment ignored
#       OUT, LA2:D05, nWR, write strobe   # text after 3rd comma ignored
#       IO , LA3:D08, D7 // comment
#   - Aliases are sanitized to [A-Za-z0-9_] and deduplicated per ROLE/LA by appending __D##
#   - No recapture required; this operates on LA1.vcd, LA2.vcd, LA3.vcd already in the dir.
#
#  python3 python/combine_sync_snap_single_r3p3.py \
#  -d ./la1010 -c ./LA1010_config.txt --sync D1 \
#  -o SYNC_ALIGNED.vcd
#

import argparse, re, sys, time
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Dict, List, Tuple

# ------------------ Config parsing ------------------

@dataclass
class ChanDef:
    la: str        # 'LA1'/'LA2'/'LA3'
    d: int         # 0..15
    alias: str     # pin name
    role: str      # 'INPUTS'|'OUTPUTS'|'IO'|'OTHER'

def parse_config(cfg: Path) -> Dict[Tuple[str,int], ChanDef]:
    """
    Accept lines like:
      IN , LA1:D00, A0                  # address bit 0
      OUT, LA2:D05, nWR, write strobe
      IO , LA3:D08, D7 // data bit 7
    Take only the alias token after the 3rd comma, stop at first comment delimiter or extra comma.
    """
    role_map = {'IN':'INPUTS','OUT':'OUTPUTS','IO':'IO'}
    m: Dict[Tuple[str,int], ChanDef] = {}
    for raw in cfg.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or s.upper().startswith(('DEFINE', 'PWM')):
            continue
        r = re.match(r'^(IN|OUT|IO)\s*,\s*(LA[123]):D(\d{1,2})\s*,\s*(.+)$', s, flags=re.IGNORECASE)
        if not r:
            continue
        role_tok, la, dstr, alias_field = r.groups()

        # Stop at first comment delimiter or extra comma
        alias_field = re.split(r'\s*(?:#|//|;|--|,)\s*', alias_field, maxsplit=1)[0]
        alias_field = alias_field.strip().strip('\'"')
        if not alias_field:
            continue

        role = role_map.get(role_tok.upper(), 'OTHER')
        m[(la, int(dstr))] = ChanDef(la=la, d=int(dstr), alias=alias_field, role=role)
    return m

def clean_alias(s: str) -> str:
    s = s.strip()
    s = re.sub(r'[^A-Za-z0-9_]', '_', s)  # remove scope breakers
    s = re.sub(r'_+', '_', s)
    if not s:
        s = "SIG"
    if s[0].isdigit():
        s = "N_" + s
    return s

# ------------------ VCD parsing ------------------

@dataclass
class VCDParsed:
    timescale: str
    id2ref: Dict[str, str]                 # idcode -> net name
    events: List[Tuple[int, str, str]]     # (time, '0'|'1'|'x'|'z', idcode)
    init_vals: Dict[str, str]              # idcode -> '0'|'1'|'x'|'z'

def read_vcd_text(p: Path):
    lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == '$enddefinitions $end')
    except StopIteration:
        raise RuntimeError(f"Malformed VCD: {p}")
    return lines[:i+1], lines[i+1:]

def parse_header(h: List[str]):
    ts = '1ns'; id2ref = {}
    for ln in h:
        m = re.search(r'\$timescale\s+(.+?)\s+\$end', ln)
        if m:
            ts = m.group(1).strip()
    for ln in h:
        m = re.match(r'^\$var\s+\w+\s+\d+\s+(\S+)\s+(\S+)\s+\$end', ln)
        if m:
            id2ref[m.group(1)] = m.group(2)
    return ts, id2ref

def collect_dumpvars_initials(body: List[str], id2ref: Dict[str, str]):
    init = {}; in_dump = False
    for ln in body:
        s = ln.strip()
        if s == '$dumpvars':
            in_dump = True
            continue
        if in_dump:
            if s == '$end':
                in_dump = False
                continue
            if s and s[0] in '01xXzZ':
                # map idcode by suffix match
                for k in range(1, 32):
                    frag = ln[-k:]
                    if frag in id2ref:
                        init[frag] = s[0].lower()
                        break
    return init

def normalize_events(body: List[str]):
    ev = []; in_dump = False; t = 0
    for ln in body:
        if not ln:
            continue
        s = ln.strip()
        if s == '$dumpvars':
            in_dump = True
            continue
        if in_dump:
            if s == '$end':
                in_dump = False
            continue
        if s.startswith('#'):
            m = re.match(r'^\#\s*(\d+)\s*(.*)$', s)
            if not m:
                continue
            t = int(m.group(1)); rest = m.group(2)
            if rest:
                for tok in re.finditer(r'([01xXzZ])(\S+)', rest):
                    ev.append((t, tok.group(1).lower(), tok.group(2)))
            continue
        m = re.match(r'^([01xXzZ])(\S+)$', s)
        if m:
            ev.append((t, m.group(1).lower(), m.group(2)))
    return ev

def parse_vcd(p: Path) -> VCDParsed:
    hdr, body = read_vcd_text(p)
    ts, id2ref = parse_header(hdr)
    init = collect_dumpvars_initials(body, id2ref)
    ev = normalize_events(body)
    for (t, v, i) in ev:
        if t == 0 and i not in init and v in '01xz':
            init[i] = v
    return VCDParsed(ts, id2ref, ev, init)

# ------------------ SYNC edges & masks ------------------

@dataclass
class SyncEdges:
    rise: List[int]
    fall: List[int]
    hi_w: List[int]
    lo_w: List[int]

def extract_sync_edges(vcd: VCDParsed, name: str) -> SyncEdges:
    ids = [i for i, n in vcd.id2ref.items() if n == name]
    if not ids:
        raise RuntimeError(f"{name} not found.")
    iid = ids[0]
    cur = vcd.init_vals.get(iid)
    R, F = [], []
    for (t, v, i) in vcd.events:
        if i != iid or v not in '01':
            continue
        if cur is None:
            cur = v
            continue
        if cur == '0' and v == '1':
            R.append(t)
        elif cur == '1' and v == '0':
            F.append(t)
        cur = v
    if F and R and F[0] < R[0]:
        F = F[1:]
    n = min(len(R), len(F))
    R, F = R[:n], F[:n]
    HI = [F[k] - R[k] for k in range(n)]
    LO = [R[k+1] - F[k] for k in range(n-1)] + ([HI[-1]] if n else [])
    return SyncEdges(R, F, HI, LO)

def build_valid_cycles(all_edges: Dict[str, SyncEdges], alpha: float, min_ticks: int) -> List[int]:
    def mask(se: SyncEdges):
        if not se.hi_w:
            return []
        med_hi = max(1, int(median(se.hi_w)))
        med_lo = max(1, int(median(se.lo_w)))
        thr_hi = max(min_ticks, int(alpha * med_hi))
        thr_lo = max(min_ticks, int(alpha * med_lo))
        ok = []
        for k in range(min(len(se.hi_w), len(se.lo_w))):
            ok.append(se.hi_w[k] >= thr_hi and se.lo_w[k] >= thr_lo)
        return ok
    masks = {la: mask(se) for la, se in all_edges.items()}
    nmin = min(len(m) for m in masks.values() if m)
    used = []
    for k in range(max(0, nmin - 1)):   # need k+1 for low-mid
        if all(masks[la][k] for la in masks):
            used.append(k)
    return used

# ------------------ Step sampler ------------------

class StepSampler:
    def __init__(self, w: List[Tuple[int, str]], init: str):
        self.w = w
        self.i = 0
        self.cur = init if init in '01' else '0'
    def at(self, t: int) -> str:
        w, i = self.w, self.i
        while i < len(w) and w[i][0] <= t:
            if w[i][1] in '01':
                self.cur = w[i][1]
            i += 1
        self.i = i
        return '1' if self.cur == '1' else '0'

def build_wave(vcd: VCDParsed, name: str):
    ids = [i for i, n in vcd.id2ref.items() if n == name]
    if not ids:
        raise RuntimeError(f"{name} not found.")
    iid = ids[0]
    cur = vcd.init_vals.get(iid, 'x')
    w = []
    for (t, v, i) in vcd.events:
        if i != iid or v not in '01xz':
            continue
        if not w or w[-1][1] != v:
            w.append((t, v))
    return w, (cur if cur in '01xz' else 'x')

# ------------------ Writer ------------------

def idcodes():
    alpha = [chr(c) for c in range(33, 127)]
    for a in alpha:
        yield a
    for a in alpha:
        for b in alpha:
            yield a + b

def begin_scope(f, name): f.write(f"$scope module {name} $end\n")
def end_scope(f): f.write("$upscope $end\n")

def write_vcd(out: Path, timescale: str, decl_keys: List[str], key2name: Dict[str, str],
              events: Dict[int, List[Tuple[str, str]]]):
    key2id = {k: code for k, code in zip(decl_keys, idcodes())}
    with out.open('w', encoding='utf-8') as f:
        f.write("$date\n  " + time.asctime() + "\n$end\n")
        f.write("$version\n  combine_sync_snap_single r3p3\n$end\n")
        f.write(f"$timescale {timescale} $end\n")

        # SYNC
        begin_scope(f, "SYNC")
        for la in ('LA1', 'LA2', 'LA3'):
            begin_scope(f, la)
            k = f"SYNC|{la}|SYNC"
            f.write(f"$var wire 1 {key2id[k]} SYNC $end\n")
            end_scope(f)
        end_scope(f)

        # Roles
        for role in ('INPUTS', 'OUTPUTS', 'IO', 'OTHER'):
            has_role = any(k.startswith(role + '|') for k in decl_keys)
            if not has_role:
                continue
            begin_scope(f, role)
            for la in ('LA1', 'LA2', 'LA3'):
                any_la = False
                for k in [kk for kk in decl_keys if kk.startswith(role + '|' + la + '|')]:
                    if not any_la:
                        begin_scope(f, la); any_la = True
                    f.write(f"$var wire 1 {key2id[k]} {key2name[k]} $end\n")
                if any_la:
                    end_scope(f)
            end_scope(f)

        f.write("$enddefinitions $end\n")
        f.write("#0\n")
        for k in decl_keys:
            f.write(f"0{key2id[k]}\n")
        for t in sorted(events.keys()):
            lst = events[t]
            if not lst:
                continue
            f.write(f"#{t}\n")
            for (val, k) in lst:
                f.write(f"{val}{key2id[k]}\n")

# ------------------ Main ------------------

def main():
    ap = argparse.ArgumentParser(description="Align D1 and retime signals (single rail per pin).")
    ap.add_argument('-d', '--dir', required=True, help='Dir with LA1.vcd, LA2.vcd, LA3.vcd')
    ap.add_argument('-c', '--config', required=True, help='LA1010_config.txt')
    ap.add_argument('--sync', default='D1', help='SYNC net name (default D1)')
    ap.add_argument('--roles', default='INPUTS,OUTPUTS,IO',
                    help='Comma list of roles to include (default includes OUTPUTS). Options: INPUTS,OUTPUTS,IO,OTHER')
    ap.add_argument('--alpha', type=float, default=0.25, help='Glitch filter fraction of median (SYNC)')
    ap.add_argument('--min-ticks', type=int, default=1, help='Minimum half-cycle width (ticks)')
    ap.add_argument('-o', '--out', default='SYNC_ALIGNED.vcd', help='Output VCD filename (in --dir)')
    args = ap.parse_args()

    indir = Path(args.dir)
    cfgp = Path(args.config)
    vcdp = {la: indir / f"{la}.vcd" for la in ('LA1', 'LA2', 'LA3')}
    for la, p in vcdp.items():
        if not p.exists():
            sys.exit(f"Missing {p}")
    if not cfgp.exists():
        sys.exit(f"Missing config: {cfgp}")

    cfg = parse_config(cfgp)
    roles_keep = {r.strip().upper() for r in args.roles.split(',') if r.strip()}

    # Parse VCDs & edges
    vcds = {la: parse_vcd(p) for la, p in vcdp.items()}
    tss = {v.timescale for v in vcds.values()}
    if len(tss) != 1:
        sys.exit(f"Timescales differ: {tss}")
    ts = tss.pop()

    edges = {la: extract_sync_edges(vcds[la], args.sync) for la in ('LA1', 'LA2', 'LA3')}
    used = build_valid_cycles(edges, args.alpha, args.min_ticks)
    if not used:
        sys.exit("No valid SYNC cycles after glitch filtering.")
    ref_la = max(edges.keys(), key=lambda k: len(edges[k].rise))
    Rref = [edges[ref_la].rise[k] for k in used]
    Fref = [edges[ref_la].fall[k] for k in used]

    # Build samplers for channels present in cfg with desired roles
    def build_wave(vcd, name):
        ids = [i for i, n in vcd.id2ref.items() if n == name]
        if not ids:
            raise RuntimeError(f"{name} not found.")
        iid = ids[0]; cur = vcd.init_vals.get(iid, 'x'); w = []
        for (t, v, i) in vcd.events:
            if i != iid or v not in '01xz':
                continue
            if not w or w[-1][1] != v:
                w.append((t, v))
        return w, (cur if cur in '01xz' else 'x')

    class StepSampler:
        def __init__(self, w, init):
            self.w = w; self.i = 0; self.cur = init if init in '01' else '0'
        def at(self, t):
            w, i = self.w, self.i
            while i < len(w) and w[i][0] <= t:
                if w[i][1] in '01': self.cur = w[i][1]
                i += 1
            self.i = i
            return '1' if self.cur == '1' else '0'

    # Per LA/role lists and samplers
    include: Dict[str, Dict[str, List[int]]] = {la: {'INPUTS': [], 'OUTPUTS': [], 'IO': [], 'OTHER': []}
                                                for la in ('LA1', 'LA2', 'LA3')}
    alias_raw: Dict[str, Dict[int, str]] = {la: {} for la in ('LA1', 'LA2', 'LA3')}
    alias_clean: Dict[str, Dict[int, str]] = {la: {} for la in ('LA1', 'LA2', 'LA3')}
    samp: Dict[str, Dict[int, StepSampler]] = {la: {} for la in ('LA1', 'LA2', 'LA3')}
    role_of: Dict[str, Dict[int, str]] = {la: {} for la in ('LA1', 'LA2', 'LA3')}

    for la in ('LA1', 'LA2', 'LA3'):
        for (kla, d), info in cfg.items():
            if kla != la:
                continue
            role = info.role.upper()
            if role not in roles_keep:
                continue
            net = f"D{info.d}"
            w, init = build_wave(vcds[la], net)
            samp[la][info.d] = StepSampler(w, init)
            alias_raw[la][info.d] = info.alias
            alias_clean[la][info.d] = clean_alias(info.alias)
            include[la][role].append(info.d)
            role_of[la][info.d] = role
        for r in include[la]:
            include[la][r].sort()

    # Midpoints
    hi_mid = {la: [(edges[la].rise[k] + edges[la].fall[k]) // 2 for k in used] for la in ('LA1', 'LA2', 'LA3')}
    lo_mid = {la: [(edges[la].fall[k] + edges[la].rise[k+1]) // 2 for k in used if (k+1) < len(edges[la].rise)]
              for la in ('LA1', 'LA2', 'LA3')}

    # Build declaration keys & names (unique per ROLE/LA) and mapping back to channel d
    # key format: "{ROLE}|{LA}|{UNIQUE_ALIAS}"
    decl: List[str] = []
    key2name: Dict[str, str] = {}
    rev_key_to_d: Dict[Tuple[str, str, str], int] = {}

    # SYNC rails
    for la in ('LA1', 'LA2', 'LA3'):
        k = f"SYNC|{la}|SYNC"
        decl.append(k); key2name[k] = "SYNC"

    # Roles (deterministic order)
    for role in ('INPUTS', 'OUTPUTS', 'IO', 'OTHER'):
        if role not in roles_keep:
            continue
        for la in ('LA1', 'LA2', 'LA3'):
            used_names = set()
            for d in include[la][role]:
                base = alias_clean[la][d]
                nm = base
                while (nm in used_names) or ((role, la, nm) in rev_key_to_d):
                    nm = f"{base}__D{d:02d}"
                used_names.add(nm)
                k = f"{role}|{la}|{nm}"
                decl.append(k); key2name[k] = nm
                rev_key_to_d[(role, la, nm)] = d

    # Build events at aligned edges only
    events: Dict[int, List[Tuple[str, str]]] = {}
    last: Dict[str, str] = {}

    def emit(t: int, val: str, key: str):
        events.setdefault(t, []).append((val, key))
        last[key] = val

    # posedge: SYNC=1; assign HIGH-mid samples
    for idx, tR in enumerate(Rref):
        for la in ('LA1', 'LA2', 'LA3'):
            emit(tR, '1', f"SYNC|{la}|SYNC")
        for role in roles_keep:
            for la in ('LA1', 'LA2', 'LA3'):
                if idx >= len(hi_mid[la]):
                    continue
                tm = hi_mid[la][idx]
                # iterate decl keys to keep names consistent
                for k in [kk for kk in decl if kk.startswith(role + '|' + la + '|')]:
                    _, kla, nm = k.split('|', 2)
                    d = rev_key_to_d.get((role, kla, nm))
                    if d is None:
                        continue
                    v = samp[la][d].at(tm)
                    if last.get(k) != v:
                        emit(tR, v, k)

    # negedge: SYNC=0; assign LOW-mid samples
    for idx, tF in enumerate(Fref):
        for la in ('LA1', 'LA2', 'LA3'):
            emit(tF, '0', f"SYNC|{la}|SYNC")
        for role in roles_keep:
            for la in ('LA1', 'LA2', 'LA3'):
                if idx >= len(lo_mid[la]):
                    continue
                tm = lo_mid[la][idx]
                for k in [kk for kk in decl if kk.startswith(role + '|' + la + '|')]:
                    _, kla, nm = k.split('|', 2)
                    d = rev_key_to_d.get((role, kla, nm))
                    if d is None:
                        continue
                    v = samp[la][d].at(tm)
                    if last.get(k) != v:
                        emit(tF, v, k)

    outp = Path(args.out) if Path(args.out).is_absolute() else (indir / args.out)
    write_vcd(outp, ts, decl, key2name, events)
    print(f"[OK] Wrote {outp}")
    print(f"[OK] Roles: {', '.join(sorted(roles_keep))}; ref grid: {ref_la}; cycles: {len(Rref)}")

if __name__ == "__main__":
    main()
