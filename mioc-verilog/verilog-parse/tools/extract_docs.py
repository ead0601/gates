# === VNLT TOOL ===
# file: tools/extract_docs.py
# note: Extract @help/@manual tagged comment blocks into Markdown.
# === /VNLT TOOL ===

import os, io, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYROOT = os.path.join(ROOT, "python")

TAG_RE = re.compile(r"^#\s*@(?P<tag>help|manual)\s+(?P<ident>[A-Za-z0-9_./-]+)\s*$")

def iter_py_files(root):
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.endswith('.py'):
                yield os.path.join(dp, f)

def extract_blocks(src_text):
    out = {}
    lines = src_text.splitlines()
    i = 0
    while i < len(lines):
        m = TAG_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        tag = m.group('tag')
        ident = m.group('ident')
        i += 1
        buf = []
        while i < len(lines):
            st = lines[i].strip()
            if not st.startswith('#'):
                break
            if st.startswith('# @'):
                break
            if st.startswith('# '):
                buf.append(st[2:])
            elif st == '#':
                buf.append('')
            else:
                buf.append(st[1:].lstrip())
            i += 1
        out[(tag, ident)] = "\n".join(buf).rstrip()
    return out

def main():
    docs = {}
    for path in iter_py_files(PYROOT):
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                src = f.read()
        except Exception:
            continue
        blocks = extract_blocks(src)
        for (tag, ident), text in blocks.items():
            docs.setdefault(ident, {})[tag] = text

    out = []
    out.append('# VNLT Manual\n')
    for ident in sorted(docs.keys()):
        out.append(f'## {ident}\n')
        if 'help' in docs[ident]:
            out.append(docs[ident]['help'] + '\n')
        if 'manual' in docs[ident]:
            out.append('### Details\n')
            out.append(docs[ident]['manual'] + '\n')
    sys.stdout.write("\n".join(out))

if __name__ == '__main__':
    main()
