#!/usr/bin/env python3
# mult-la1010-cap-r5.py
# Revision: r5 (2025-09-16)
#
# Purpose:
#   Capture from three Kingst LA1010s using sigrok-cli, with configurable trigger channel and edge,
#   and convert the .sr files to per-LA VCDs. This script is CAPTURE-ONLY (no combining/retiming).
#
# Key differences vs older script:
#   • New: --trig-channel (e.g., D0..D15). Default D0.
#   • Robust time handling: always passes --samples to sigrok-cli (computes from --time if needed).
#   • Voltage threshold: float like 2.5 becomes '2.5-2.5' (what LA1010 expects).
#   • Reads LA connections from LA1010_config.txt lines like:  DEFINE LA1:conn=3.23
#
# Usage example:
#   python3 mult-la1010-cap-r5.py \
#     -i ./LA1010_config.txt -o ./la1010 \
#     --samplerate 16M --samples 4000000 \
#     --trig-channel D0 --trig-edge r \
#     --threshold 2.5 --keep-pretrigger
#
#
#    ./python/mult-la1010-cap-r5.py \
#    -i ./LA1010_config.txt   -o ./la1010 \
#    --samplerate 16M --samples 1000000 \
#    --trig-channel D0 --trig-edge r \
#    --threshold 1.6
#
# After capture, you can align/retime with your other tools.

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# ---------------------------- config parsing ----------------------------

def parse_config_conns(cfg_path: Path) -> Dict[str, str]:
    """
    Parse LA connections from config lines like:
      DEFINE LA1:conn=3.23
      DEFINE LA2:conn=3.21
      DEFINE LA3:conn=3.25
    Returns dict: {'LA1': '3.23', 'LA2': '3.21', 'LA3': '3.25'}
    """
    conns: Dict[str, str] = {}
    text = cfg_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    for raw in text:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^DEFINE\s+(LA[123]):conn=([0-9]+\.[0-9]+)\s*$', line, re.I)
        if m:
            conns[m.group(1).upper()] = m.group(2)
    return conns

# ---------------------------- helpers ----------------------------

def norm_dchan(ch: str) -> str:
    """
    Normalize D-channel token:
      'D0'/'D00' -> 'D0', 'D01' -> 'D1', ..., 'D15' -> 'D15'
    """
    ch = ch.strip().upper()
    m = re.match(r'^D0*([0-9]|1[0-5])$', ch)
    if m:
        return f"D{int(m.group(1))}"
    # already Dn?
    m = re.match(r'^D(1[0-5]|[0-9])$', ch)
    if m:
        return f"D{int(m.group(1))}"
    raise ValueError(f"Invalid D-channel: {ch}. Expected D0..D15 (or D00..D15).")

def fmt_threshold(val: Optional[str]) -> Optional[str]:
    """
    LA1010 expects voltage_threshold like '2.5-2.5' or '1.6-1.6'.
    Accepts: None, '2.5', '2.5-2.5', '1.6-1.6'.
    """
    if val is None:
        return None
    s = str(val).strip().lower()
    if re.match(r'^\d+(\.\d+)?-\d+(\.\d+)?$', s):
        return s
    m = re.match(r'^\d+(\.\d+)?$', s)
    if m:
        f = m.group(0)
        return f"{f}-{f}"
    raise ValueError(f"Invalid threshold '{val}'. Use e.g. 2.5 or 2.5-2.5 or 1.6-1.6")

def samplerate_to_int(s: str) -> int:
    """
    Convert samplerate like '16M' or '28.8M' to samples/sec integer.
    Supports k/M/G suffix. Rounds to nearest int.
    """
    s = s.strip()
    m = re.match(r'^(\d+(\.\d+)?)([kKmMgG])?$', s)
    if not m:
        raise ValueError(f"Invalid samplerate '{s}'. Examples: 16M, 500k, 1G")
    num = float(m.group(1))
    suf = (m.group(3) or '').upper()
    mult = {'K': 1e3, 'M': 1e6, 'G': 1e9}.get(suf, 1.0)
    hz = int(round(num * mult))
    return hz

def compute_samples(samplerate: str, samples: Optional[int], time_s: Optional[float]) -> int:
    if samples is not None:
        return int(samples)
    if time_s is not None:
        hz = samplerate_to_int(samplerate)
        return int(round(hz * float(time_s)))
    raise ValueError("Either --samples or --time must be provided.")

def run_cmd(cmd: list, label: str) -> Tuple[int, str, str]:
    """
    Run a subprocess, return (rc, stdout, stderr).
    """
    print(f"[{label}] RUN: {' '.join(shlex.quote(c) for c in cmd)}")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    rc = p.returncode
    if rc != 0:
        print(f"[{label}] sigrok-cli failed (rc={rc}). stderr:\n{err}", file=sys.stderr)
    return rc, out, err

# ---------------------------- main capture logic ----------------------------

def build_capture_cmd(conn: str, out_sr: Path, trig_channel: str, trig_edge: str,
                      samplerate: str, samples: int, threshold_fmt: Optional[str]) -> list:
    # full 16 channels
    chans = ",".join([f"D{i}" for i in range(16)])
    cmd = [
        "sigrok-cli",
        "-d", f"kingst-la1010:conn={conn}",
        "--channels", chans,
        "--config", f"samplerate={samplerate}",
    ]
    if threshold_fmt:
        cmd += ["--config", f"voltage_threshold={threshold_fmt}"]
    cmd += [
        "--samples", str(samples),
        "-t", f"{trig_channel}={trig_edge}",
        "-O", "srzip",
        "-o", str(out_sr)
    ]
    return cmd

def build_convert_cmd(in_sr: Path, out_vcd: Path) -> list:
    return [
        "sigrok-cli",
        "-I", "srzip",
        "-i", str(in_sr),
        "-O", "vcd",
        "-o", str(out_vcd)
    ]

def main():
    ap = argparse.ArgumentParser(description="Capture from three LA1010s and convert to VCD (capture-only).")
    ap.add_argument("-i", "--input", required=True, help="LA1010_config.txt (must contain DEFINE LA#:conn=.. lines)")
    ap.add_argument("-o", "--outdir", required=True, help="Output directory for .sr and .vcd")
    ap.add_argument("--samplerate", required=True, help="Samplerate, e.g., 16M, 28.8M")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--samples", type=int, help="Total samples to acquire per device")
    grp.add_argument("--time", type=float, help="Capture time in seconds (converted to samples)")
    ap.add_argument("--trig-channel", default="D0", help="Trigger channel (D0..D15). Default D0")
    ap.add_argument("--trig-edge", default="r", choices=["0","1","r","f","e"], help="Trigger edge/level")
    ap.add_argument("--threshold", type=str, default=None, help="Voltage threshold (e.g., 2.5 or 2.5-2.5 or 1.6-1.6)")
    ap.add_argument("--sequential", action="store_true", help="Capture LAs one-by-one (recommended)")
    ap.add_argument("--convert-only", action="store_true", help="Skip capture; only convert existing .sr -> .vcd")
    ap.add_argument("--force", action="store_true", help="Overwrite existing .sr/.vcd")
    args = ap.parse_args()

    cfg = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Parse connections
    conns = parse_config_conns(cfg)
    missing = [la for la in ("LA1","LA2","LA3") if la not in conns]
    if missing:
        sys.exit(f"Missing conn definitions in {cfg}: {missing}. Expected lines like 'DEFINE LA1:conn=3.23'.")

    # Normalize trigger channel
    try:
        trig_ch = norm_dchan(args.trig_channel)
    except ValueError as e:
        sys.exit(str(e))

    # Format voltage threshold
    try:
        thr_fmt = fmt_threshold(args.threshold)
    except ValueError as e:
        sys.exit(str(e))

    # Compute samples
    try:
        total_samples = compute_samples(args.samplerate, args.samples, args.time)
    except ValueError as e:
        sys.exit(str(e))

    # Plan capture order (sequential default)
    order = ["LA1","LA2","LA3"]

    # Capture + convert per LA
    any_fail = False
    for la in order:
        conn = conns[la]
        sr_path = outdir / f"{la}.sr"
        vcd_path = outdir / f"{la}.vcd"

        if not args.convert_only:
            if sr_path.exists() and not args.force:
                print(f"[{la}] NOTE: {sr_path.name} exists (use --force to overwrite). Skipping capture.")
            else:
                # remove old files if any
                if sr_path.exists(): sr_path.unlink()
                if vcd_path.exists(): vcd_path.unlink()
                cmd = build_capture_cmd(conn, sr_path, trig_ch, args.trig_edge, args.samplerate, total_samples, thr_fmt)
                rc, _, _ = run_cmd(cmd, la)
                if rc != 0:
                    any_fail = True
                    print(f"[{la}] ERROR: capture failed; skipping conversion.", file=sys.stderr)
                    continue
        else:
            if not sr_path.exists():
                print(f"[{la}] NOTE: {sr_path.name} not found; skipping conversion.")
                continue

        # Convert .sr -> .vcd
        if sr_path.exists():
            cmd2 = build_convert_cmd(sr_path, vcd_path)
            rc2, _, err2 = run_cmd(cmd2, la)
            if rc2 != 0:
                any_fail = True
            else:
                print(f"[{la}] OK: wrote {vcd_path.name}")
        else:
            print(f"[{la}] NOTE: {sr_path.name} not found after capture; skipping conversion.")

        # If running sequentially, proceed one-by-one (default). If not, the above is still sequential.
        # (Parallel mode could be added later; sequential is safer on USB bandwidth.)

    if any_fail:
        sys.exit(1)

if __name__ == "__main__":
    main()
