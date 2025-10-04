# === VNLT REV ===
# file: python/cmd_gui.py
# rev:  2025-10-03  r1  by:ediaz  tag:read
# note: initial per-file revision header; build & load design from manifest
# === /VNLT REV ===

# Launch the HTML5 GUI by exporting JSON and inlining it into the viewer HTML.

from typing import List, Optional
import os
import json
import webbrowser
from pathlib import Path
import re

import registry as _reg  # uses REG and CommandRegistry

SUMMARY = "gui [--html FILE] [--to FILE] [--json FILE] [--no-open] — export and open the HTML GUI"
DETAIL = """\
Usage:
  gui
  gui --html graph_view_step1.html
  gui --to ./gui-view.html
  gui --json ./graph-for-gui.json
  gui --no-open

What it does:
  1) Ensures a design is loaded (via 'read verilog <manifest>' or '-m').
  2) Runs 'export json' to produce the annotated netlist JSON.
  3) Inlines that JSON into the HTML viewer as: window.VNLT_GRAPH = {...};
  4) Writes a new HTML file (default: ./gui-view.html).
  5) Opens it in your default browser (omit with --no-open).

Options:
  --html FILE     Path to the base viewer HTML. Default: ./graph_view_step1.html
  --to FILE       Output HTML path to write.  Default: ./gui-view.html
  --json FILE     Where to write/read the exported JSON. Default: ./graph-for-gui.json
  --no-open       Do not open a browser after writing the HTML.

Notes:
  - This injector replaces ANY 'window.VNLT_GRAPH = ...;' assignment (including '|| {}'),
    ensuring the data is available BEFORE viewer scripts execute.
  - If no assignment is found, it injects a <script> BEFORE the first <script> tag.
"""

DEFAULT_HTML = "html/graph_view_ffcenter.html"
DEFAULT_JSON = "volatile/gui-graph.json"
DEFAULT_OUT = "volatile/gui-view.html"

def _parse_args(argv: List[str]):
    html = None
    out_html = None
    json_path = None
    open_flag = True

    tokens = list(argv or [])
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "--html" and i + 1 < len(tokens):
            html = tokens[i + 1]
            i += 2
        elif t == "--to" and i + 1 < len(tokens):
            out_html = tokens[i + 1]
            i += 2
        elif t == "--json" and i + 1 < len(tokens):
            json_path = tokens[i + 1]
            i += 2
        elif t == "--no-open":
            open_flag = False
            i += 1
        else:
            i += 1

    return {
        "html": html or DEFAULT_HTML,
        "to": out_html or DEFAULT_OUT,
        "json": json_path or DEFAULT_JSON,
        "open": open_flag,
    }


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _write_text(path: Path, text: str):
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def _inject_json_into_html(html_text: str, graph_obj) -> (str, str):
    """
    Replace an existing 'window.VNLT_GRAPH = ...;' (robust), or inject BEFORE the first <script>.
    Returns (new_html_text, where_msg).
    """
    json_text = json.dumps(graph_obj, ensure_ascii=False, indent=2)
    assign_line = f"window.VNLT_GRAPH = {json_text};"

    # 1) Replace ANY assignment to window.VNLT_GRAPH, including "|| {}" defaults
    # Matches: window.VNLT_GRAPH = <anything until semicolon> ;
    pat_any_assign = re.compile(r"(window\.VNLT_GRAPH\s*=\s*)([^;]*)(;)", re.DOTALL)
    if pat_any_assign.search(html_text):
        new_text = pat_any_assign.sub(rf"\1{json_text}\3", html_text, count=1)
        return new_text, "replaced existing window.VNLT_GRAPH assignment"

    # 2) If no assignment exists, inject BEFORE the first <script ...>
    m = re.search(r"<script\b", html_text, flags=re.IGNORECASE)
    if m:
        idx = m.start()
        inject_block = f"<script>\n{assign_line}\n</script>\n"
        new_text = html_text[:idx] + inject_block + html_text[idx:]
        return new_text, "injected data script before first <script> tag"

    # 3) Else, try injecting inside <head> if present
    mhead = re.search(r"</head>", html_text, flags=re.IGNORECASE)
    if mhead:
        idx = mhead.start()
        inject_block = f"<script>\n{assign_line}\n</script>\n"
        new_text = html_text[:idx] + inject_block + html_text[idx:]
        return new_text, "injected data script at end of <head>"

    # 4) Fallback: inject before </body> (may be too late in some pages, but last resort)
    mbody = re.search(r"</body>", html_text, flags=re.IGNORECASE)
    if mbody:
        idx = mbody.start()
        inject_block = f"<script>\n{assign_line}\n</script>\n"
        new_text = html_text[:idx] + inject_block + html_text[idx:]
        return new_text, "injected data script before </body>"

    # 5) Absolute fallback: append at end
    new_text = html_text + f"\n<script>\n{assign_line}\n</script>\n"
    return new_text, "appended data script at end of document"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(argv: List[str], interp) -> Optional[dict]:
    if not getattr(interp, "graph", None):
        return {"__raw": "ERROR: No design loaded. Use 'read verilog <manifest>' first.\n"}

    args = _parse_args(argv)
    html_in = Path(args["html"]).resolve()
    out_html = Path(args["to"]).resolve()
    json_path = Path(args["json"]).resolve()

    # 1) Export annotated JSON using the existing 'export json' command
    try:
        _ = _reg.REG.execute(f"export json --to {json_path}", interp)
    except Exception as e:
        return {"__raw": f"ERROR: failed to run 'export json': {e}\n"}

    if not json_path.exists():
        return {"__raw": f"ERROR: export did not create JSON at {json_path}\n"}

    try:
        graph_obj = _load_json(json_path)
    except Exception as e:
        return {"__raw": f"ERROR: could not read JSON '{json_path}': {e}\n"}

    if not html_in.exists():
        return {"__raw": f"ERROR: viewer HTML not found: {html_in}\n"}
    try:
        html_text = _read_text(html_in)
    except Exception as e:
        return {"__raw": f"ERROR: could not read HTML '{html_in}': {e}\n"}

    # 2) Inject JSON assignment early enough so the viewer sees it
    final_text, where_msg = _inject_json_into_html(html_text, graph_obj)

    # 3) Write output HTML
    try:
        _write_text(out_html, final_text)
    except Exception as e:
        return {"__raw": f"ERROR: failed to write output HTML '{out_html}': {e}\n"}

    # 4) Open in browser (unless --no-open)
    msg = f"Wrote GUI HTML to {out_html}\nUsing JSON {json_path}\nBase viewer {html_in}\nInjection: {where_msg}\n"
    if args["open"]:
        try:
            webbrowser.open(out_html.as_uri())
            msg += "Opened in default browser.\n"
        except Exception as e:
            msg += f"[WARN] could not open browser automatically: {e}\n"

    # Meta counts (if present)
    try:
        nc = graph_obj.get("_meta", {}).get("node_count")
        ec = graph_obj.get("_meta", {}).get("edge_count")
        if nc is not None and ec is not None:
            msg += f"Graph: nodes={nc} edges={ec}\n"
    except Exception:
        pass

    return {"__raw": msg}


def register(reg: _reg.CommandRegistry):
    # Your registry API: add_command(name, handler, summary, detail=None, aliases=None)
    reg.add_command("gui", run, SUMMARY, DETAIL)
