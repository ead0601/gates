# rev:  2025-10-08  r12  by: ediaz  tag: gui
"""
GUI command: always-inline viewer (newplace-direct)
- Exports volatile/graph.json (via cmd_export)
- Builds volatile/graph_view_ffcenter.inline.html by inlining window.VNLT_GRAPH
- Strips any loader code (external or inline fetch) from the base HTML
- Opens the inline HTML unless --no-open is supplied
- --newplace calls placement_gen.generate() directly (no argparse)

Args (r2-style):
  gui [--newplace] [--html FILE] [--json FILE] [--to FILE] [--no-open]

Defaults:
  --html  html/graph_view_ffcenter.html            (base template)
  --json  volatile/graph.json                      (export path)
  --to    volatile/graph_view_ffcenter.inline.html (inline output)
"""

from __future__ import annotations
import json
import re
import webbrowser
from pathlib import Path
import importlib.util as _iu

import registry as _reg         # CommandRegistry (r2-style)
import cmd_export as _cmd_export

SUMMARY = "Launch the HTML GUI with the current design (always-inline data)."
DETAIL = """\
gui
    Export design to volatile/graph.json, build an inline HTML at
    volatile/graph_view_ffcenter.inline.html (no network fetch), and open it.

gui --newplace
    Deterministically regenerate data-in/placement.csv via placement_gen.generate(),
    then proceed as above.

Options:
    --html FILE   Base HTML template (default: html/graph_view_ffcenter.html)
    --json FILE   JSON output path (default: volatile/graph.json)
    --to   FILE   Inline HTML output (default: volatile/graph_view_ffcenter.inline.html)
    --no-open     Do not open the viewer after generation.
"""

# ---------- helpers ----------

def _repo_root() -> Path:
    # .../verilog-parse/python/cmd_gui.py -> repo root is parent of 'python'
    return Path(__file__).resolve().parent.parent

def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def _safe_inline_json(obj) -> str:
    """Serialize JSON safe for embedding in <script> tag."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    # Avoid closing the script tag accidentally if data ever contained it.
    return s.replace("</script>", "<\\/script>")

def _strip_external_loader(html: str) -> str:
    """Remove any <script ... graph.loader.js ...></script> tags."""
    pattern = re.compile(
        r'\s*<script[^>]+src=["\'][^"\']*?/js/graph\.loader\.js(?:\.r\d+)?["\'][^>]*>\s*</script>\s*',
        re.IGNORECASE,
    )
    return pattern.sub("\n", html)

def _strip_inline_fetch_blocks(html: str) -> str:
    """
    Remove inline <script> blocks that fetch graph.json or are labeled as inline loader.
    """
    pattern = re.compile(
        r'<script[^>]*>\s*(?:<!--)?(?:(?:(?!</script>).)*?(?:File:\s*inline\s+graph\.loader\.js|fetch\(\s*[\'"]graph\.json[\'"]))(?:(?!</script>).)*?</script>',
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub("\n", html)

def _insert_before_app_core(html: str, block: str) -> str:
    """
    Insert `block` immediately before the first <script ... js/app.core.js ...>.
    Fallbacks: before </head>, else before </body>, else prepend.
    """
    app_pat = re.compile(
        r'(<script[^>]+src=["\'][^"\']*?/js/app\.core\.js(?:\.r\d+)?["\'][^>]*>\s*</script>)',
        re.IGNORECASE,
    )
    m = app_pat.search(html)
    if m:
        start = m.start()
        return html[:start] + block + "\n" + html[start:]

    # Fallbacks
    for tag in ("</head>", "</HEAD>", "</body>", "</BODY>"):
        idx = html.find(tag)
        if idx != -1:
            return html[:idx] + block + "\n" + html[idx:]
    return block + "\n" + html

def _add_inline_revision_banner(block_after: str) -> str:
    """Standard top-of-file revision comment for the generated inline viewer."""
    banner = [
        "<!-- =============================================================== -->",
        "<!-- rev:  2025-10-08  r12  by: ediaz  tag: gui-inline              -->",
        "<!-- Revision: r12 (2025-10-08)                                      -->",
        "<!-- Always-inline build: window.VNLT_GRAPH embedded; no fetch.      -->",
        "<!-- =============================================================== -->",
        "",
    ]
    return "\n".join(banner) + block_after

def _build_inline_html(base_html: Path, json_path: Path, out_html: Path) -> None:
    """
    Read base HTML, strip loaders, embed window.VNLT_GRAPH, write inline HTML.
    """
    html = base_html.read_text(encoding="utf-8", errors="ignore")

    # Strip loaders to ensure file:// safe inline
    html = _strip_external_loader(html)
    html = _strip_inline_fetch_blocks(html)

    # Load graph.json (must exist)
    data = json.loads(json_path.read_text(encoding="utf-8", errors="ignore"))
    inline_block = (
        "<script>\n"
        "/* window.VNLT_GRAPH (always-inline) */\n"
        "window.VNLT_GRAPH = " + _safe_inline_json(data) + ";\n"
        "</script>"
    )

    # Insert inline data BEFORE app.core.js so app sees it at init
    html = _insert_before_app_core(html, inline_block)

    # Add revision banner at top (keeps base file untouched)
    html = _add_inline_revision_banner(html)

    _ensure_dir(out_html)
    out_html.write_text(html, encoding="utf-8")

def _open_in_browser(p: Path) -> None:
    try:
        # Prefer file:// to ensure no network requirement
        url = p.resolve().as_uri()
        webbrowser.open_new_tab(url)
    except Exception:
        pass

def _do_newplace_direct(repo: Path, interpreter=None) -> None:
    """
    Import placement_gen directly from file and call generate() only.
    Avoids argparse and any argv bleed-through.
    """
    mod_path = (repo / "python" / "placement_gen.py").resolve()
    spec = _iu.spec_from_file_location("placement_gen", str(mod_path))
    if not spec or not spec.loader:
        return
    pg = _iu.module_from_spec(spec)
    try:
        spec.loader.exec_module(pg)  # type: ignore[attr-defined]
    except Exception:
        return
    gen = getattr(pg, "generate", None)
    if callable(gen):
        try:
            # Call with interpreter if available; out_path uses the module default
            gen(interpreter=interpreter)
        except Exception:
            # Silent continue; placement.csv might already exist
            pass

# ---------- command entrypoint (r2-style) ----------

def run(argv, interpreter=None):
    repo = _repo_root()
    volatile = repo / "volatile"
    html_dir = repo / "html"

    # Defaults
    base_html = html_dir / "graph_view_ffcenter.html"
    json_out = volatile / "graph.json"
    inline_out = volatile / "graph_view_ffcenter.inline.html"
    open_flag = True
    do_newplace = False

    # Minimal arg parsing (r2-style)
    it = iter(argv or [])
    for tok in it:
        if tok == "--no-open":
            open_flag = False
        elif tok == "--newplace":
            do_newplace = True
        elif tok == "--html":
            base_html = Path(next(it, str(base_html)))
        elif tok == "--json":
            json_out = Path(next(it, str(json_out)))
        elif tok == "--to":
            inline_out = Path(next(it, str(inline_out)))
        else:
            # ignore unknowns to stay lenient with prior revs
            pass

    if do_newplace:
        _do_newplace_direct(repo, interpreter)

    # Ensure JSON export (always overwrite)
    _ensure_dir(json_out)
    _cmd_export.run(["json", "--to", str(json_out)], interpreter)

    # Build inline HTML (no fetch, file:// safe)
    _build_inline_html(base_html, json_out, inline_out)

    # Open unless suppressed
    if open_flag:
        _open_in_browser(inline_out)

    # Return a small status dict for shells/tests (optional)
    return {
        "json": str(json_out),
        "html": str(inline_out),
        "opened": bool(open_flag),
        "mode": "always-inline",
    }

def register(registry):
    # r2-style registration so it appears in help
    registry.add_command("gui", run, SUMMARY, DETAIL)
