================================================================================
Options Reference (in order)
================================================================================

1) mult-la1010-cap.py  —  Capture from three LA1010s and (optionally) convert
--------------------------------------------------------------------------------
Synopsis:
  python3 mult-la1010-cap.py \
    -i LA1010_config.txt \
    -o ./la1010 \
    --samplerate 16M \
    (--samples 4000000 | --time 1.0) \
    [--trig-channel D0] [--trig-edge {0,1,r,f,e}] \
    [--sync-edge {r,f,e}] \
    [--threshold 2.5] \
    [--timeout 20] \
    [--keep-pretrigger] \
    [--sequential] \
    [--convert-only] \
    [--force]

Required:
  -i, --input           Path to LA1010_config.txt (device conns, channel roles/names).
  -o, --outdir          Output directory for LAx.sr / LAx.vcd.

Acquisition:
  --samplerate <RATE>   Sample rate for all devices, e.g. 16M, 8M.
  --samples <N>         Total samples to acquire (integer). Exactly one of --samples/--time.
  --time <SEC>          Duration to acquire in seconds (float). Exactly one of --samples/--time.
  --threshold <V>       Logic threshold in volts (e.g., 2.5). Script maps to driver’s format (e.g., 2.5-2.5).
  --timeout <SEC>       Per-device host-side timeout guard (seconds).

Trigger & sync:
  --trig-channel D#     Trigger channel (e.g., D0, D1). (Use if your script version supports it.)
  --trig-edge {0,1,r,f,e}
                        Trigger condition: 0=low, 1=high, r=rise, f=fall, e=edge.
  --sync-edge {r,f,e}   Optional capture sync hint (passed to driver where applicable).
  --keep-pretrigger     Keep pre-trigger samples (if driver supports pretrigger buffer).

Execution mode:
  --sequential          Capture LA1→LA2→LA3 in series (workaround for flaky USB). Default: parallel.
  --convert-only        Skip capture; convert any existing LAx.sr → LAx.vcd in --outdir.
  --force               Overwrite existing .sr/.vcd files in --outdir.

Outputs:
  <outdir>/LA1.sr, LA2.sr, LA3.sr (if captured)
  <outdir>/LA1.vcd, LA2.vcd, LA3.vcd (if converted)

Notes:
  • Ensure the config’s conn= values match current USB IDs.
  • “Device only sent … samples” → reduce samplerate or samples.
  • “No supported PWM … skipping” → those optional keys are ignored by the driver.


2) combine_sync_snap_single.py  —  Align D1 across LA1/2/3 and retime signals
--------------------------------------------------------------------------------
Synopsis:
  python3 combine_sync_snap_single.py \
    -d ./la1010 \
    -c LA1010_config.txt \
    --sync D1 \
    [--roles INPUTS,OUTPUTS,IO] \
    [--alpha 0.25] \
    [--min-ticks 1] \
    -o SYNC_ALIGNED.vcd

Required:
  -d, --dir             Directory containing LA1.vcd, LA2.vcd, LA3.vcd.
  -c, --config          LA1010_config.txt (lines like: IN , LA2:D05, nRD  # comment).

Key options:
  --sync <D#>           Name of the master clock in each VCD (default: D1).
  --roles <CSV>         Which roles to include in the output VCD scopes.
                        Choices: INPUTS, OUTPUTS, IO, OTHER (e.g., --roles INPUTS,OUTPUTS,IO).
  --alpha <0..1>        Glitch filter as a fraction of the median half-cycle width (D1). Default 0.25.
  --min-ticks <N>       Absolute minimum half-cycle width (in VCD ticks). Default 1.
  -o, --out <FILE>      Output VCD filename (written inside -d unless absolute path).

Behavior:
  • Aligns D1 (SYNC) across LA1/2/3.
  • Retime policy (“snap-back” DDR): sample at mid-HIGH → apply at posedge; sample at mid-LOW → apply at negedge.
  • Emits one rail per pin (no _POS/_NEG), grouped by role and LA:
      SYNC → LAx → SYNC
      INPUTS/OUTPUTS/IO → LAx → <alias>

Name handling:
  • Aliases are taken from the 3rd CSV field; trailing comments or extra commas are ignored.
    (Comment delimiters: # // ; -- ,)
  • Aliases sanitized to [A-Za-z0-9_] and de-duplicated within ROLE/LA (appends __D## if needed).

Requirements & notes:
  • All input VCDs must share the same $timescale.
  • Pins present in config but missing from a VCD are skipped (warning printed).


3) make_mem_from_sync_vcd.py  —  Emit Verilog $readmemb vectors from synced VCD
--------------------------------------------------------------------------------
Synopsis:
  python3 make_mem_from_sync_vcd.py \
    -c LA1010_config.txt \
    -v SYNC_ALIGNED.vcd \
    -o ./verilog_vectors \
    [--sync-la LA1|LA2|LA3]

Required:
  -c, --config          LA1010_config.txt (defines INPUTS/OUTPUTS per LA and their order).
  -v, --vcd             SYNC_ALIGNED.vcd (from the combiner; single-rail, grouped scopes).
  -o, --outdir          Output directory for generated files.

Key options:
  --sync-la <LAx>       Which SYNC rail to use as inputs bit[0] (default: LA1).

What it writes (into --outdir):
  inputs_both_edges.mem   One line per aligned D1 edge (R0, F0, R1, F1, …).
                          Bit 0 = SYNC, then all INPUTS in config order (LA1, then LA2, then LA3).
                          Lines include trailing comments: // k=<cycle> edge=R|F t=<tick>
  inputs_both_edges.map   Bit index → label mapping (e.g., “0 SYNC”, “1 LA1:A0”, …).

  outputs_both_edges.mem  One line per aligned D1 edge; OUTPUTS only (no SYNC).
  outputs_both_edges.map  Bit index → label mapping for outputs.

Notes:
  • Vectors are 0/1 only (no x/z); they correspond to the retimed midpoints at each D1 edge.
  • Ordering strictly follows config-file appearance per LA.
  • Any configured alias not found in the VCD scope is omitted with a warning (bit-width reduces accordingly).

--------------------------------------------------------------------------------
Typical Flow:
  (1) mult-la1010-cap.py         → LA1/LA2/LA3.vcd
  (2) combine_sync_snap_single.py → SYNC_ALIGNED.vcd (aligned & retimed; named & grouped)
  (3) make_mem_from_sync_vcd.py   → inputs_both_edges*.mem/.map, outputs_both_edges*.mem/.map
================================================================================
