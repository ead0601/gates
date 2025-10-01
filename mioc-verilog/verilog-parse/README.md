# Verilog Netlist CLI — v0.6.5 Additions & User Guide

This guide documents **new and changed functionality** since the earlier README and consolidates common workflows and examples.

> Built on the existing README (features, core commands, traversal notes). See that file for background.

## What’s New in v0.6.5

### CLI & UX
- **`-m, --manifest`**: start the REPL with a manifest auto-loaded. Example: `./vlnt -m ./verilog_manifest.txt`
- **History & line editing**: Arrow keys / tab completion; history persisted to `~/.vnlt_history`.
- **Exit commands**: `quit` / `exit` cleanly leave the REPL.
- **Output redirection**: `>` or `>>` to send any command output to a file.
- **UNIX-style pipelines**: `|` to pipe vnlt output to a shell command, and **`$( ... )`** form.

### New Commands
- **`ls`**: list files in the current working directory.
- **`cat <path>`**: print a file’s contents.

### Listing & Finding
- **`list files`**: show what the manifest resolved (kind, path, status, size, mtime).
- **`list components`**: filter with `--like`, `--seq|--comb`, and `--ports` to print port names.
- **`list instances`**: `--like`, `--type CTYPE`, `--seq|--comb` views; totals fanin/fanout/net counts.
- **`list pins <INST>`** or `list pins --like 'U*.A*'`.
- **`list port [--like GLOB]`**: *globs are case-sensitive and do not require quotes*.
- **`list nets [--like GLOB] [--dangling] [--multi-driver] [--show-ends] [--limit N]`**.

- **`find components|instance|pin|port|net PATTERN`**: shell-style globs `* ? [abc]`, **case-sensitive**.

### Traversal
- **`fanin <target>`**: `--tree`, `--endpoints`, `--cross-ff`, `--depth`, `--branch`.
- **`fanout <target>`**: `--endpoints`, `--depth` (comb-only forward traversal).
- **`paths --from A[,B,…] --to X[,Y,…]`**: no FF crossing; supports `--depth`, `--max-paths`.

### Parser & Netgraph Semantics
- **Assign elimination**: **all `assign` statements** (even inside the top module body) are compiled into concrete instances, never shown as textual assigns.
  - Non-inverting ⇒ **`iobuf`** (1-in/1-out comb)
  - Inverting ⇒ **`iobuf_n`**
  - Instances auto-named **`io1`, `io2`, …**
- **No “assign_*” wrappers** appear in `list instances`.
- **Top alias policy**: `PIN_IN_*` are **aliases only**; not promoted to ports.

## Quick Reference — Common Tasks

```text
./vlnt -m ./verilog_manifest.txt
list files
list port
list instances --seq
list instances --comb

find components *flop*
find instance u2*
find pin U23.A
find net w_*

list components --like mioc_xnor2 --ports
list pins u23
list nets --like RA7 --show-ends

fanin RA7 --tree --cross-ff
fanout w_u23z --endpoints
paths --from BA6,BA7 --to RA7 --depth 500 --max-paths 50

fanin RA7 --tree --cross-ff | grep flop | awk '{print $1}' | sort -u
fanin RA7 --tree --cross-ff | $(grep flop | awk '{print $1}' | sort -u)
fanin RA7 --tree --cross-ff > ra7_fanin.txt
```

## Manifest Tips

```text
top: mioc_top
seq_cells: mioc_flop

rtl: ./rtl/mioc_flop_rtl.v
rtl: ./rtl/mioc_nor2_rtl.v
rtl: ./rtl/mioc_nor3_rtl.v
rtl: ./rtl/mioc_nand2_rtl.v
rtl: ./rtl/mioc_nand4_nor2_rtl.v
rtl: ./rtl/mioc_inv1_rtl.v
rtl: ./rtl/mioc_xnor2_rtl.v

components: ./mioc_top.v   # assigns inside top are compiled into iobuf / iobuf_n
```

## Version
Covers **v0.6.5**.
