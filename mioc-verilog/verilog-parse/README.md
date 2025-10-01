# VNLT — Verilog Netlist CLI
## Command Reference — v0.6.6 (Comprehensive)

This is the canonical, exhaustive reference for **VNLT v0.6.6**. It documents **every command**,
**every option**, target notation, shell features, and scripting, with copy‑pasteable examples.

---

## Table of Contents
- [1. Overview & Quick Start](#1-overview--quick-start)
- [2. Installation & Invocation](#2-installation--invocation)
  - [2.1 Entrypoint & Wrapper](#21-entrypoint--wrapper)
  - [2.2 Global Flags](#22-global-flags)
  - [2.3 Batch Mode](#23-batch-mode)
- [3. Shell Integration](#3-shell-integration)
  - [3.1 Piping & Command Substitution](#31-piping--command-substitution)
  - [3.2 Redirection](#32-redirection)
- [4. REPL Scripting](#4-repl-scripting)
  - [4.1 Variables](#41-variables)
  - [4.2 Foreach Loops](#42-foreach-loops)
- [5. Targets & Globs](#5-targets--globs)
- [6. Commands](#6-commands)
  - [6.1 `help`](#61-help)
  - [6.2 `exit` / `quit`](#62-exit--quit)
  - [6.3 `read verilog`](#63-read-verilog)
  - [6.4 `list files`](#64-list-files)
  - [6.5 `list components`](#65-list-components)
  - [6.6 `list instances`](#66-list-instances)
  - [6.7 `list pins`](#67-list-pins)
  - [6.8 `list port`](#68-list-port)
  - [6.9 `list nets`](#69-list-nets)
  - [6.10 `find`](#610-find)
  - [6.11 `show`](#611-show)
  - [6.12 `fanin`](#612-fanin)
  - [6.13 `fanout`](#613-fanout)
  - [6.14 `paths`](#614-paths)
  - [6.15 `ls`](#615-ls)
  - [6.16 `cat`](#616-cat)
- [7. Parser Semantics](#7-parser-semantics)
- [8. Tips & Recipes](#8-tips--recipes)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Version](#10-version)

---

## 1. Overview & Quick Start

```text
./vlnt -m ./verilog_manifest.txt
list files
list port
list components --seq --ports
list instances --seq
fanin RA7 --tree --cross-ff | grep -E '\.q(bar)?$' | awk -F'.' '{print $1}' | sort -u
```

---

## 2. Installation & Invocation

### 2.1 Entrypoint & Wrapper
- Entrypoint: `python/verilog_parse.py` (invoked via `./vlnt`).
- Version banner: `vnlt v0.6.6 — Verilog Netlist CLI`.

### 2.2 Global Flags
- `-m, --manifest <path>`: Load a Verilog manifest at startup.
- `--graph <netgraph.json>`: Load a prebuilt graph (optional).
- `-y, --batch <file>`: Run commands from a file (blank lines and `#` comments ignored).

### 2.3 Batch Mode
```text
# jobs/fanin_all_ports.vnl
set ports = $(list port | grep -E '\bout\b' | awk '{print $1}')
foreach p in $ports do fanin ${p} --tree --cross-ff > out/${p}.txt end
```
```bash
./vlnt -m verilog_manifest.txt -y jobs/fanin_all_ports.vnl
```

---

## 3. Shell Integration

### 3.1 Piping & Command Substitution
- **Pipe**: `|` sends VNLT output to your shell (`grep`, `awk`, `sort`, etc.).
- **Wrapper**: optional `$( ... )` after `|` to group a shell pipeline.
```text
fanin RA7 --tree --cross-ff | grep flop | awk '{print $1}' | sort -u
fanin RA7 --tree --cross-ff | $(grep flop | awk '{print $1}' | sort -u)
```

### 3.2 Redirection
- `>` write, `>>` append (parsed at the end of the line).
```text
fanin RA7 --tree --cross-ff > ra7_fanin.txt
list instances --seq >> seq_summary.txt
```

---

## 4. REPL Scripting

### 4.1 Variables
- `set NAME = $( <vnlt-cmd> [| shell ...] )` → capture final text, newline‑split into a list.
- `set NAME = literal1 "literal 2 with spaces"` → literal list.

Inspect / remove:
```text
vars
vars NAME
unset NAME
```

### 4.2 Foreach Loops
- `foreach item in $NAME [--echo] [--limit N] do <vnlt-cmd-with-$item> end`
- `$item` / `${item}` interpolation happens **before** parsing pipes/redirects.
- Body supports `|`, `>`, `>>` per iteration.

Examples:
```text
set ports = $(list port | grep -E '\bout\b' | awk '{print $1}')
foreach p in $ports --echo --limit 3 do fanin ${p} --tree --cross-ff > ${p}.txt end

foreach p in $ports do       fanin ${p} --tree --cross-ff | grep -E '\.q(bar)?$' | awk -F'.' '{print $1}' | sort -u > ${p}.flops.txt     end
```

---

## 5. Targets & Globs
- **Ports**: `PORT:<name>` (e.g., `PORT:RA7`). Often just `RA7` works.
- **Nets**: `NET:<name>` (e.g., `NET:w_u23z`).
- **Pins**: `<instance>.<pin>` (e.g., `u54.q`).
- **Instances**: `<instance>` (e.g., `u54`, `io3`).
- **Cell types**: `mioc_flop`, `mioc_nor2`, etc.
- **Globs**: `* ? [abc]` (case‑sensitive). Quotes are not required for `--like`.

---

## 6. Commands

### 6.1 `help`
**Usage**
```text
help
help <cmd>
```
**Description**: List all commands or detailed help for `<cmd>`.
**Examples**
```text
help
help fanin
```

### 6.2 `exit` / `quit`
Cleanly exit the REPL.
```text
quit
exit
```

### 6.3 `read verilog`
**Usage**
```text
read verilog <manifest.lst|.txt>
```
**Manifest fields**
- `top: <top_module_name>`
- `seq_cells: <ff_cell_type>`
- `rtl: <path>` (repeatable; primitive cells for pin directions)
- `components: <path>` (structural Verilog including the top)
- *(assigns inside the top body are compiled into instances — see §7)*
**Examples**
```text
read verilog verilog_manifest.txt
list files
```

### 6.4 `list files`
Show manifest‑resolved files with status metadata.
```text
list files
```

### 6.5 `list components`
**Usage**
```text
list components [--like PATTERN] [--seq|--comb] [--ports]
```
**Description**
- `--seq` sequential only; `--comb` combinational only.
- `--ports` prints the port list for each cell type.
**Examples**
```text
list components
list components --seq
list components --like mioc_* --ports
```

### 6.6 `list instances`
**Usage**
```text
list instances [--like PATTERN] [--type CTYPE] [--seq|--comb]
```
**Description**
- `--like` filter by instance name (glob).
- `--type` filter by cell type (e.g., `mioc_flop`, `iobuf`).
- `--seq` sequential only; `--comb` combinational only.
**Examples**
```text
list instances
list instances --seq
list instances --like 'u7*'
list instances --type mioc_flop
```

### 6.7 `list pins`
**Usage**
```text
list pins <INSTANCE>
list pins --like 'U*.A*'
```
**Description**: Show pins for an instance or expand a pin glob across instances.
**Examples**
```text
list pins u23
list pins --like 'u*.q*'
```

### 6.8 `list port`
**Usage**
```text
list port [--like PATTERN]
```
**Description**: Show top‑level ports (name, direction, net).
**Examples**
```text
list port
list port --like 'RA*'
```

### 6.9 `list nets`
**Usage**
```text
list nets [--like PATTERN] [--dangling] [--multi-driver] [--show-ends] [--limit N]
```
**Description**
- `--dangling`: dangling nets only.
- `--multi-driver`: nets with multiple drivers.
- `--show-ends`: print drivers/sinks for each net.
- `--limit N`: cap verbose endpoint expansion.
**Examples**
```text
list nets
list nets --like 'w_*' --show-ends --limit 20
list nets --dangling
list nets --multi-driver
```

### 6.10 `find`
**Usage**
```text
find components PATTERN
find instance PATTERN
find pin PATTERN
find port PATTERN
find net PATTERN
```
**Notes**
- Globs `* ? [abc]`, case‑sensitive.
- `--long` prints additional descriptors when available.
**Examples**
```text
find components *flop*
find instance u2*
find pin u2*.q
find port RA*
find net w_* --long
```

### 6.11 `show`
**Usage**
```text
show <TARGET>
```
**Description**
- `PORT:<name>` → port metadata
- `NET:<name>` → driver/sinks
- `<instance>` → cell type + pin map
- `<instance>.<pin>` → direction + net
**Examples**
```text
show PORT:RA7
show NET:RA7
show u54
show u54.q
```

### 6.12 `fanin`
**Usage**
```text
fanin <target> [--tree] [--endpoints] [--cross-ff] [--stage-limit N] [--depth N] [--branch N]
```
**Modes & Options**
- Default (no flags): JSON cone summary (nets, instances, edges) up to `--depth` (default 200).
- `--tree`: indented tree output.
- `--endpoints`: only terminal sources (TOP_IN / CONST).
- `--cross-ff`: allow crossing sequential elements.
- `--stage-limit N`: cap number of FF stages when crossing.
- `--depth N`: limit traversal depth (default 200).
- `--branch N`: cap children per node in tree mode.
**Examples**
```text
fanin RA7 --tree
fanin RA7 --tree --cross-ff
fanin u54.q --endpoints
fanin NET:w_u23z --depth 500
fanin RA7 --tree --cross-ff | grep -E '\.q(bar)?$' | awk -F'.' '{print $1}' | sort -u
```

### 6.13 `fanout`
**Usage**
```text
fanout <target> [--endpoints] [--depth N]
```
**Description**: Combinational fan‑out (does not cross FFs).
**Examples**
```text
fanout u23.z
fanout RA7 --endpoints
fanout NET:w_foo --depth 100
```

### 6.14 `paths`
**Usage**
```text
paths --from SRC[,SRC,...] --to DST[,DST,...] [--depth N] [--max-paths N]
```
**Description**: Enumerate **combinational** paths (no FF crossing).
**Examples**
```text
paths --from BA6,BA7 --to RA7 --depth 500 --max-paths 50
paths --from u54.q --to RA7
```

### 6.15 `ls`
List files in the current working directory.
```text
ls
```

### 6.16 `cat`
Print a file’s contents.
```text
cat verilog_manifest.txt
cat out/RA7.txt
```

---

## 7. Parser Semantics
- All textual `assign` statements (including inside the top module) are compiled into instances:
  - Non‑inverting → `iobuf` (1‑in/1‑out)
  - Inverting → `iobuf_n`
  - Instances auto‑named `io1`, `io2`, …
- No `assign_*` wrappers; `io* : iobuf/iobuf_n` appear in listings.
- `PIN_IN_*` are aliases only; not promoted to ports.

---

## 8. Tips & Recipes
- Large cones: prefer `--endpoints` or summarize via shell.
- “Which flops feed PORT X?”
  ```text
  fanin PORT:X --tree --cross-ff | grep -E '\.q(bar)?$' | awk -F'.' '{print $1}' | sort -u
  ```
- Save a cone for diffing:
  ```text
  fanin RA7 --tree --cross-ff > out/RA7_fanin.txt
  ```

---

## 9. Troubleshooting
- Globs/patterns are **case‑sensitive**.
- “Unknown instance/pin”: check case and that the graph is loaded (`read verilog ...`).
- “No drivers” in fan‑in: net may be tied/alias or outside current depth/flags.
- `cmd_paths` warnings: check file syntax for stray line‑continuations.

---

## 10. Version
This reference matches **VNLT v0.6.6**.
