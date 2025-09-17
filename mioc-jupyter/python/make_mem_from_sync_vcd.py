#!/usr/bin/env python3
# make_mem_from_sync_vcd_r1.py
# Revision: r1 (2025-09-16)
#
# Purpose
#   Read:
#     - LA1010_config.txt  (to know INPUT/OUTPUT pins & ordering)
#     - SYNC_ALIGNED.vcd   (retimed, aligned, single-rail per pin)
#   Write (to -o output dir):
#     - inputs_both_edges.mem    # 1 line per D1 edge: [SYNC | all INPUT bits in config order (LA1,LA2,LA3)]
#     - inputs_both_edges.map    # bit index → label (SYNC, LAx:<alias>)
#     - outputs_both_edges.mem   # 1 line per D1 edge: [all OUTPUT bits in config order (LA1,LA2,LA3)]
#     - outputs_both_edges.map   # bit index → label (LAx:<alias>)
#
#   Lines are emitted in chronological order of the retimed VCD edges:
#     R0, F0, R1, F1, ...
#   Each line ends with a helpful comment (ignored by $readmemb):
#     // k=<cycle_index> edge=R|F t=<vcd_time_tick>
#
# Usage
#   python3 make_mem_from_sync_vcd_r1.py \
#     -c ./LA1010_config.txt \
#     -v ./la1010/SYNC_ALIGNED.vcd \
#     -o ./verilog_vectors
#
# Notes
#   - SYNC bit (bit 0 of inputs) is taken from SYNC/LA1/SYNC by default (all three SYNC rails are identical).
#   - INPUT/OUTPUT ordering follows the order they appear in LA1010_config.txt *per LA*.
#   - Aliases are sanitized to [A-Za-z0-9_] and de-duplicated per ROLE+LA by appending "__D##" (same rule as combiner).
#   - If an alias from the config can’t be found in the VCD (scope/name mismatch), a warning is printed and that bit is
#     omitted from the vector (bit-count reduces accordingly).
#   - IO pins are not included by default (this script emits only INPUTS to inputs*.mem and OUTPUTS to outputs*.mem).
#     If you want IO included, let me know and I’ll add a flag.
#
# Outputs
#   outdir/
#     inputs_both_edges.mem
#     inputs_both_edges.map
#     outputs_both_edges.mem
#     outputs_both_edges.map
#
#  python3 python/make_mem_from_sync_vcd_r1.py \
#  -c ./LA1010_config.txt  -v ./la1010/SYNC_ALIGNED.vcd \
#  -o ./verilog_vectors
#
#

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# ------------------ config parsing (same rules as combiner) ------------------

@dataclass
class ChanDef:
    la: str        # 'LA1'|'LA2'|'LA3'
    d: int         # 0..15
    alias: str     # pin name (raw)
    role: str      # 'INPUTS'|'OUTPUTS'|'IO'|'OTHER'

def clean_alias(s: str) -> str:
    s = s.strip()
    s = re.sub(r'[^A-Za-z0-9_]', '_', s)     # remove scope breakers
    s = re.sub(r'_+', '_', s)
    if not s:
        s = "SIG"
    if s[0].isdigit():
        s = "N_" + s
    return s

def parse_config(cfg: Path) -> List[ChanDef]:
    """
    Accept lines like:
      IN , LA1:D00, A0                  # address bit 0
      OUT, LA2:D05, nWR, write strobe
      IO , LA3:D08, D7 // data bit 7
    We take only the alias token after the 3rd comma, stopping at the first comment delimiter or extra comma.
    Preserve file order.
    """
    role_map = {'IN':'INPUTS','OUT':'OUTPUTS','IO':'IO'}
    out: List[ChanDef] = []
    for raw in cfg.read_text(encoding='utf-8', errors='ignore').splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or s.upper().startswith(('DEFINE','PWM')):
            continue
        m = re.match(r'^(IN|OUT|IO)\s*,\s*(LA[123]):D(\d{1,2})\s*,\s*(.+)$', s, flags=re.IGNORECASE)
        if not m:
            continue
        role_tok, la, dstr, alias_field = m.groups()
        # stop at comment or extra comma
        alias_field = re.split(r'\s*(?:#|//|;|--|,)\s*', alias_field, maxsplit=1)[0]
        alias_field = alias_field.strip().strip('\'"')
        if not alias_field:
            continue
        out.append(ChanDef(la=la, d=int(dstr), alias=alias_field, role=role_map.get(role_tok.upper(), 'OTHER')))
    return out

# ------------------ VCD parsing with scopes ------------------

@dataclass
class VCDVar:
    idcode: str
    ref: str
    scope: Tuple[str, ...]  # e.g., ('INPUTS','LA1')

@dataclass
class VCDData:
    # header
    timescale: str
    # maps
    id2var: Dict[str, VCDVar]
    pathref2id: Dict[Tuple[Tuple[str,...], str], str]
    # events
    events: List[Tuple[int, str, str]]  # (time, value '0'|'1'|'x'|'z', idcode)

def parse_vcd_with_scopes(path: Path) -> VCDData:
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    # header
    scope_stack: List[str] = []
    id2var: Dict[str, VCDVar] = {}
    pathref2id: Dict[Tuple[Tuple[str,...], str], str] = {}
    timescale = '1ns'
    i = 0
    # parse header until $enddefinitions
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1; continue
        if ln.startswith('$timescale'):
            m = re.match(r'^\$timescale\s+(.+?)\s+\$end$', ln)
            if m:
                timescale = m.group(1).strip()
        elif ln.startswith('$scope'):
            m = re.match(r'^\$scope\s+module\s+(.+?)\s+\$end$', ln)
            if m:
                scope_stack.append(m.group(1))
        elif ln.startswith('$upscope'):
            if scope_stack:
                scope_stack.pop()
        elif ln.startswith('$var'):
            # $var wire 1 <id> <ref> $end
            m = re.match(r'^\$var\s+\w+\s+\d+\s+(\S+)\s+(\S+)\s+\$end$', ln)
            if m:
                idc, ref = m.groups()
                scope_tuple = tuple(scope_stack)
                id2var[idc] = VCDVar(idcode=idc, ref=ref, scope=scope_tuple)
                pathref2id[(scope_tuple, ref)] = idc
        elif ln == '$enddefinitions $end':
            i += 1
            break
        i += 1

    # body: normalize events including inline '#t <assigns>'
    events: List[Tuple[int, str, str]] = []
    in_dump = False
    tcur = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if not s:
            continue
        if s == '$dumpvars':
            in_dump = True
            continue
        if in_dump:
            if s == '$end':
                in_dump = False
            else:
                m = re.match(r'^([01xXzZ])(\S+)$', s)
                if m:
                    events.append((tcur, m.group(1).lower(), m.group(2)))
            continue
        if s.startswith('#'):
            m = re.match(r'^\#\s*(\d+)\s*(.*)$', s)
            if not m:
                continue
            tcur = int(m.group(1))
            rest = m.group(2)
            if rest:
                for tok in re.finditer(r'([01xXzZ])(\S+)', rest):
                    events.append((tcur, tok.group(1).lower(), tok.group(2)))
            continue
        m = re.match(r'^([01xXzZ])(\S+)$', s)
        if m:
            events.append((tcur, m.group(1).lower(), m.group(2)))
    return VCDData(timescale, id2var, pathref2id, events)

# ------------------ helpers: build the exact names used in VCD ------------------

def build_role_order(cfg_items: List[ChanDef], role: str) -> Dict[str, List[int]]:
    """
    Return channels by LA for given role, preserving file order.
    { 'LA1': [d,...], 'LA2': [...], 'LA3': [...] }
    """
    out = {'LA1': [], 'LA2': [], 'LA3': []}
    for it in cfg_items:
        if it.role.upper() == role.upper():
            out[it.la].append(it.d)
    return out

def build_alias_tables(cfg_items: List[ChanDef], role: str) -> Dict[str, Dict[int, str]]:
    """
    For a given role, compute sanitized, unique alias per LA & channel d,
    following the same rule as our combiner (append __D## if duplicate in ROLE+LA).
    Returns: { LAx: { d: unique_alias, ... }, ... }
    """
    # Gather per LA in file order
    per_la = {'LA1': [], 'LA2': [], 'LA3': []}
    for it in cfg_items:
        if it.role.upper() == role.upper():
            per_la[it.la].append(it)

    result: Dict[str, Dict[int, str]] = {'LA1': {}, 'LA2': {}, 'LA3': {}}
    for la in ('LA1','LA2','LA3'):
        used = set()
        for it in per_la[la]:
            base = clean_alias(it.alias)
            nm = base
            while nm in used:
                nm = f"{base}__D{it.d:02d}"
            used.add(nm)
            result[la][it.d] = nm
    return result

# ------------------ main vector generation ------------------

def main():
    ap = argparse.ArgumentParser(description="Generate $readmemb input/output vectors from a synced VCD.")
    ap.add_argument('-c','--config', required=True, help='LA1010_config.txt')
    ap.add_argument('-v','--vcd',     required=True, help='SYNC_ALIGNED.vcd')
    ap.add_argument('-o','--outdir',  required=True, help='Output directory for .mem and .map files')
    ap.add_argument('--sync-la', default='LA1', choices=['LA1','LA2','LA3'], help='Which SYNC rail to use as bit0 (default LA1)')
    args = ap.parse_args()

    cfgp = Path(args.config)
    vcdp = Path(args.vcd)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not cfgp.exists(): sys.exit(f"Missing config: {cfgp}")
    if not vcdp.exists(): sys.exit(f"Missing VCD: {vcdp}")

    # Parse config & VCD
    cfg_items = parse_config(cfgp)
    vcd = parse_vcd_with_scopes(vcdp)

    # Build ordering & aliases
    inputs_by_la  = build_role_order(cfg_items, 'INPUTS')
    outputs_by_la = build_role_order(cfg_items, 'OUTPUTS')
    inputs_alias  = build_alias_tables(cfg_items, 'INPUTS')
    outputs_alias = build_alias_tables(cfg_items, 'OUTPUTS')

    # Resolve idcodes for variables we need
    # SYNC bit (from SYNC / LA? / SYNC)
    sync_scope = ('SYNC', args.sync_la)
    sync_id = vcd.pathref2id.get((sync_scope, 'SYNC'))
    if not sync_id:
        sys.exit(f"Could not find SYNC variable at scope {sync_scope} in VCD.")

    # INPUT ids (in config order per LA)
    input_ids: List[Tuple[str,str,str,str]] = []  # (role, LA, alias, idcode)
    for la in ('LA1','LA2','LA3'):
        for d in inputs_by_la[la]:
            alias = inputs_alias[la].get(d)
            if not alias: 
                continue
            key = (('INPUTS', la), alias)
            vid = vcd.pathref2id.get(key)
            if not vid:
                print(f"[WARN] INPUT not found in VCD: {la}:D{d:02d} alias='{alias}'", file=sys.stderr)
                continue
            input_ids.append(('INPUTS', la, alias, vid))

    # OUTPUT ids (in config order per LA)
    output_ids: List[Tuple[str,str,str,str]] = []
    for la in ('LA1','LA2','LA3'):
        for d in outputs_by_la[la]:
            alias = outputs_alias[la].get(d)
            if not alias:
                continue
            key = (('OUTPUTS', la), alias)
            vid = vcd.pathref2id.get(key)
            if not vid:
                print(f"[WARN] OUTPUT not found in VCD: {la}:D{d:02d} alias='{alias}'", file=sys.stderr)
                continue
            output_ids.append(('OUTPUTS', la, alias, vid))

    # Build event timeline: group by time
    by_time: Dict[int, List[Tuple[str,str]]] = {}
    times: List[int] = []
    for (t,val,iid) in vcd.events:
        by_time.setdefault(t, []).append((val, iid))
    times = sorted(by_time.keys())

    # Initialize state for all tracked ids (default '0' if unseen)
    tracked_ids = {sync_id} | {vid for *_, vid in input_ids} | {vid for *_, vid in output_ids}
    state: Dict[str, str] = {iid: '0' for iid in tracked_ids}

    # Prepare outputs
    in_mem  = (outdir / 'inputs_both_edges.mem').open('w', encoding='utf-8')
    in_map  = (outdir / 'inputs_both_edges.map').open('w', encoding='utf-8')
    out_mem = (outdir / 'outputs_both_edges.mem').open('w', encoding='utf-8')
    out_map = (outdir / 'outputs_both_edges.map').open('w', encoding='utf-8')

    # Write mapping files
    # inputs: bit 0 = SYNC; then LA1 inputs, LA2 inputs, LA3 inputs (in that order)
    in_map.write("0 SYNC\n")
    bit_idx = 1
    for role, la, alias, vid in input_ids:
        in_map.write(f"{bit_idx} {la}:{alias}\n")
        bit_idx += 1

    # outputs: only OUTPUT pins, LA1, LA2, LA3 order
    bit_idx = 0
    for role, la, alias, vid in output_ids:
        out_map.write(f"{bit_idx} {la}:{alias}\n")
        bit_idx += 1

    # Walk timeline and emit vectors at each edge (#time).
    # Cycle index k increments at each R (SYNC==1), F uses current k.
    k = -1
    for t in times:
        # apply all assignments at this time
        for (val, iid) in by_time[t]:
            if iid in tracked_ids:
                if val in ('0','1'):
                    state[iid] = val
                else:
                    # ignore x/z (retimed VCD should not have them)
                    pass

        sync_val = state.get(sync_id, '0')
        edge = 'R' if sync_val == '1' else 'F'
        if edge == 'R':
            k += 1  # new cycle on posedge

        # Build input bits: [SYNC] + inputs in config order (per LA)
        in_bits = [sync_val]
        for role, la, alias, vid in input_ids:
            in_bits.append(state.get(vid, '0'))

        # Build output bits: outputs only
        out_bits = []
        for role, la, alias, vid in output_ids:
            out_bits.append(state.get(vid, '0'))

        # Emit lines with trailing comments
        in_mem.write(f"{''.join(in_bits)}  // k={k} edge={edge} t={t}\n")
        out_mem.write(f"{''.join(out_bits) if out_bits else ''}  // k={k} edge={edge} t={t}\n")

    in_mem.close(); in_map.close(); out_mem.close(); out_map.close()
    print(f"[OK] Wrote: {outdir / 'inputs_both_edges.mem'}")
    print(f"[OK] Wrote: {outdir / 'inputs_both_edges.map'}")
    print(f"[OK] Wrote: {outdir / 'outputs_both_edges.mem'}")
    print(f"[OK] Wrote: {outdir / 'outputs_both_edges.map'}")

if __name__ == "__main__":
    main()
