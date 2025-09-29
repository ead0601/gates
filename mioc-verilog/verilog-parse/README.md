# Verilog Netlist CLI Tool

This tool provides a command-line interface (CLI) to explore and query netlists parsed from Verilog designs.  
It is step 3 of the multi-step pipeline (after building devices and assembling the netgraph).

---

## Pipeline Steps

### Step 1: Build Device Definitions
Parses RTL files and creates per-device Python classes plus a `celllib.json`.

Example:
```bash
python3 step1_build_devices.py \
  --rtl-list ./verilog_rtl.lst \
  --out-devices ./devices \
  --out-celllib ./celllib.json \
  --seq-cells mioc_flop
```

Outputs:
- `devices/*.py` for each device
- `celllib.json`

---

### Step 2: Build Netlist Graph
Parses structural netlist and assignments, connects devices, and produces `netgraph.json`.

Example:
```bash
python3 step2_build_graph.py \
  --celllib ./celllib.json \
  --components ./mioc_components.v \
  --assigns ./mioc_pin_assignments.v \
  --out ./netgraph.json
```

Outputs:
- `netgraph.json` containing:
  - Instances
  - Nets and connectivity
  - Aliases for top ports
  - Constants

---

### Step 3: Explore with CLI
Interactive CLI or batch mode for exploring the netlist.

Examples:
```bash
# Interactive REPL
python3 step3_cli.py --graph ./netgraph.json

# Run batch commands from a file
python3 step3_cli.py --graph ./netgraph.json -y commands.txt
```

---

## Features
- Inspect nets and instances (`show`)
- Trace fan-in and fan-out cones
- Render ASCII tree diagrams for fan-in
- Collect only endpoint pins (TOP_IN / TOP_OUT / CONST)
- Explore paths between signals
- Batch mode via script files
- Interactive REPL with command history (↑/↓ arrows, persisted in `~/.vnlt_history`)

---

## Commands

### `show <target>`
Inspect a **net** (drivers/loads) or an **instance** (type, pins, connections).

Examples:
```text
show RA7
show u23
show u23.z
```

---

### `fanin <target>`
Explore what **drives** a net.

**Modes:**
- `--tree` → Pretty ASCII tree
- `--endpoints` → List only terminal sources (TOP_IN / CONST)
- Default (no flags) → JSON cone

**Traversal Options:**
- `--cross-ff` → Allow crossing flip-flops
- `--stage-limit N` → Maximum number of FF stages (omit = unlimited when crossing)
- `--depth N` → Depth cap (default: 200)
- `--branch N` → In tree mode, cap children per node (omit = unlimited)

Examples:
```text
fanin RA7 --tree --cross-ff
fanin RA7 --endpoints --cross-ff --depth 1000
fanin u44.z --tree --branch 8
```

---

### `fanout <target>`
Explore what a net **drives**.

**Modes:**
- `--endpoints` → List only terminal sinks (TOP_OUT)
- Default (no flags) → JSON cone

**Traversal:**
- Combinational forward only (does not cross FFs)
- `--depth N` → Depth cap (default: 200)

Examples:
```text
fanout w_u23z --endpoints
fanout RA7 --depth 400
```

---

### `paths --from A[,B,…] --to X[,Y,…]`
Find combinational paths from sources to sinks (no FF crossing).

**Options:**
- `--depth N` → Depth cap (default: 200)
- `--max-paths N` → Limit number of paths (default: 200)

Examples:
```text
paths --from PIN_IN_15 --to BOOTROMCS_N
paths --from BA6,BA7 --to RA7 --depth 500 --max-paths 50
```

---

## Session Control

- `quit` / `exit` → Leave the REPL
- `-y, --batch <file>` → Run commands from a file  
  (ignores blank lines and `#` comments)
- **History** → Up/Down arrows cycle past commands, persisted to `~/.vnlt_history`

---

## Output Conventions

- **Aliases:**  
  `PIN_IN_12` prints as `BA6 [TOP_IN][INV]` if assigned `~BA6`
- **[FF]** → Sequential instance
- **[crossed FF]** → Crossing through a flip-flop
- **CONST:** `1'b0` or `1'b1` shown as `[CONST ...]`
- **(loop)** → Cycle detected
- **↪ see ▲N** → Shared substructure (node seen earlier)

---

## Example Session

```text
vnlt> show RA7
vnlt> fanin RA7 --tree --cross-ff
vnlt> fanin RA7 --endpoints --cross-ff --depth 1000
vnlt> fanout RA7 --endpoints
vnlt> paths --from PIN_IN_15 --to BOOTROMCS_N
vnlt> quit
```

---

## TODO / Ideas
- Add inline `help` command (`help` or `?`) with per-command usage
- Add export options (`--json`, `--csv`) for endpoints
- Support `--hide-const` to suppress constants in output
- Support explicit `--branch 0` meaning “no cap”

---
