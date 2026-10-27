"""align_scripts.py - port PC English dialogue into decompiled PSP scene scripts (.py), pairing talk calls by order.

Usage:  python align_scripts.py PSP_PY_DIR PC_PY_DIR OUT_DIR [--wrap 50] [--rows 3] [SCENE ...]
Reads PSP/C0301.py (JP) and PC/C0301.py (EN) written by the EDDecompiler (cp932).  For every ChrTalk / NpcTalk / AnonymousTalk call:
  key = (call kind, speaker chr id); calls are paired by difflib on the key sequence (equal blocks only).
  new text = PSP's leading control codes (#290F#6P etc, kept per page) + PC English body, re-wrapped to --wrap columns, max --rows rows per page.
  NpcTalk names are taken from PC too.  Unpaired calls stay Japanese (listed in OUT_DIR/_report.txt).
Writes OUT_DIR/<scene>.py (cp932) ready for  python <scene>.py --gp=<fakegp> <outdir>   (recompile to ._SN).
"""
import os, re, sys, ast, difflib

CODE = re.compile(r'#\d*[A-Za-z]')
PREFIX = re.compile(r'^(?:#\d*[A-Za-z])+')
KINDS = ('ChrTalk', 'NpcTalk', 'AnonymousTalk')
CALL = re.compile(r'\b(ChrTalk|NpcTalk|AnonymousTalk)\(')
SUBS = {'\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"', '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00a0': ' '}


def scan_call(t, i):
    """t[i] is just after '(' ; return (end index of matching ')', list of (s,e) top-level arg spans)."""
    depth = 1; j = i; args = []; s = i; instr = False
    while j < len(t):
        c = t[j]
        if instr:
            if c == '\\': j += 2; continue
            if c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c in '([{': depth += 1
            elif c in ')]}':
                depth -= 1
                if depth == 0:
                    if t[s:j].strip(): args.append((s, j))
                    return j, args
            elif c == ',' and depth == 1:
                args.append((s, j)); s = j + 1
        j += 1
    raise ValueError('unbalanced')


TOK = re.compile(r'"(?:[^"\\]|\\.)*"|scpstr\([^)]*\)')
def parse_elems(src):
    """src = last arg source. Returns list of ('s', str) / ('t', source, is_color) or None."""
    src = src.strip()
    toks = list(TOK.finditer(src))
    rest = re.sub(r'#[^\n]*', '', TOK.sub('', src))
    if re.sub(r'[\s(),]', '', rest): return None
    out = []
    for m in toks:
        g = m.group(0)
        if g.startswith('"'):
            try: out.append(('s', ast.literal_eval(g)))
            except Exception: return None
        else:
            out.append(('t', g, 'SCPSTR_CODE_COLOR' in g))
    return out


def seg_groups(elems):
    """split elems into groups delimited by non-colour tokens. returns (groups, delimiters)"""
    groups = [[]]; delims = []
    for e in elems:
        if e[0] == 't' and not e[2]:
            delims.append(e); groups.append([])
        else:
            groups[-1].append(e)
    return groups, delims


def calls(t):
    out = []
    for m in CALL.finditer(t):
        try:
            end, args = scan_call(t, m.end())
        except ValueError:
            continue
        args = [(a, b) for a, b in args if t[a:b].strip()]
        kind = m.group(1)
        need = {'ChrTalk': 2, 'NpcTalk': 3, 'AnonymousTalk': 1}[kind]
        if len(args) < need: continue
        elems = parse_elems(t[args[-1][0]:args[-1][1]])
        if elems is None: continue
        txt = ''.join(e[1] for e in elems if e[0] == 's')
        ntok = sum(1 for e in elems if e[0] == 't' and not e[2])
        name = None
        if kind == 'NpcTalk':
            try: name = ast.literal_eval(t[args[1][0]:args[1][1]].strip())
            except Exception: name = None
        chr_ = t[args[0][0]:args[0][1]].strip() if kind != 'AnonymousTalk' else ''
        cn = None
        if kind == 'AnonymousTalk':
            mm = re.search(r'SetChrName\(("(?:[^"\\]|\\.)*")\)\s*$', t[max(0, m.start() - 160):m.start()])
            if mm: cn = (max(0, m.start() - 160) + mm.start(1), max(0, m.start() - 160) + mm.end(1))
        out.append(dict(kind=kind, chr=chr_, elems=elems, ntok=ntok, cname=cn, start=m.start(), end=end + 1, args=args, text=txt, name=name, close=end))
    return out


def width(s):
    return len(CODE.sub('', s))


def wrap_page(body, wrap):
    words = body.replace('\x01', ' ').split(' ')
    lines = []; cur = ''
    for w in words:
        if not w: continue
        if cur and width(cur) + 1 + width(w) > wrap:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w) if cur else w
    if cur: lines.append(cur)
    return lines


def clean(s):
    for a, b in SUBS.items(): s = s.replace(a, b)
    return s


def build_text(psp, pc, wrap, rows):
    """psp, pc = message strings. Pages are separated by \\x03 (each page ends with \\x02)."""
    ppages = psp.split('\x03'); cpages = pc.split('\x03')
    out = []
    for k, cp in enumerate(cpages):
        pp = ppages[min(k, len(ppages) - 1)]
        pre = PREFIX.match(pp); pre = pre.group(0) if pre else ''
        cp = clean(cp)
        endc = '\x02' if cp.endswith('\x02') else ''
        body = cp.rstrip('\x02')
        body = PREFIX.sub('', body, count=1)
        lines = wrap_page(body, wrap)
        if not lines: lines = ['']
        chunks = [lines[i:i + rows] for i in range(0, len(lines), rows)]
        for ci, ch in enumerate(chunks):
            last = ci == len(chunks) - 1
            out.append(pre + '\x01'.join(ch) + ('\x02' if (not last or endc or k < len(cpages) - 1) else '') + ('' if last and k == len(cpages) - 1 else '\x03'))
    return ''.join(out)


def lit(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\x01', '\\x01').replace('\x02', '\\x02').replace('\x03', '\\x03').replace('\x07', '\\x07') + '"'


def emit(text, indent):
    # one literal per line, split after \x01 ; single literal when only one line
    parts = re.split(r'(?<=\x01)', text)
    parts = [p for p in parts if p]
    if len(parts) == 1:
        return lit(parts[0])
    pad = ' ' * indent
    return '(\n' + ''.join(pad + '    ' + lit(p) + ',\n' for p in parts) + pad + ')'


def emit_tokens(pe, ce, indent, wrap, rows):
    pg, pd = seg_groups(pe); cg, cd = seg_groups(ce)
    if len(pg) != len(cg): return None
    pad = ' ' * indent; lines = []
    for gi, (g1, g2) in enumerate(zip(pg, cg)):
        ptxt = ''.join(e[1] for e in g1 if e[0] == 's')
        ctxt = re.sub(r'\x07.', '', ''.join(e[1] for e in g2 if e[0] == 's'))
        if ptxt or ctxt:
            first = next((i for i, e in enumerate(g1) if e[0] == 's'), len(g1))
            for e in g1[:first]: lines.append(e[1])
            if ctxt:
                trail = '\x07\x00' if '\x07\x00' in ptxt and not ctxt.endswith('\x02') else ''
                nt = build_text(ptxt, clean(ctxt), wrap, rows) if ptxt else clean(ctxt)
                for part in [x for x in re.split(r'(?<=\x01)', nt) if x]: lines.append(lit(part))
            rest = [e for e in g1[first:] if e[0] == 't']
            for e in rest: lines.append(e[1])
        else:
            for e in g1: lines.append(e[1])
        if gi < len(pd): lines.append(pd[gi][1])
    return '(\n' + ''.join(pad + '    ' + l + ',\n' for l in lines) + pad + ')'


def menus(t):
    res = []
    for m in re.finditer(r'\bMenu\(', t):
        try: end, args = scan_call(t, m.end())
        except ValueError: continue
        if len(args) < 5: continue
        el = parse_elems(t[args[-1][0]:args[-1][1]])
        if el is None or any(e[0] != 's' for e in el): continue
        res.append((args[-1], [e[1] for e in el], tuple(a for a in (t[args[0][0]:args[0][1]].strip(),))))
    return res


def port_menus(psp_t, pc_t):
    a = menus(psp_t); b = menus(pc_t)
    if len(a) != len(b): return psp_t
    out = psp_t
    for (span, ps, _), (_, pc, _) in sorted(zip(a, b), key=lambda x: -x[0][0][0]):
        if len(ps) != len(pc): continue
        if not all(any(ord(ch) > 127 for ch in x) for x in ps) or any(ord(ch) > 127 for y in pc for ch in clean(y)): continue
        new = '(\n' + ''.join('            ' + lit(clean(y)) + ',\n' for y in pc) + '        )'
        out = out[:span[0]] + ' ' + new + out[span[1]:]
    return out


def align(psp_t, pc_t, wrap=50, rows=3):
    pc_calls = calls(pc_t); ps_calls = calls(psp_t)
    ka = [(c['kind'], c['chr'], c['ntok']) for c in ps_calls]; kb = [(c['kind'], c['chr'], c['ntok']) for c in pc_calls]
    sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False)
    pairs = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal':
            pairs += [(a0 + k, b0 + k) for k in range(a1 - a0)]
    edits = []
    for ia, ib in pairs:
        p, c = ps_calls[ia], pc_calls[ib]
        ln_start = psp_t.rfind('\n', 0, p['start']) + 1
        indent = len(psp_t[ln_start:p['start']]) - len(psp_t[ln_start:p['start']].lstrip())
        a, b = p['args'][-1]
        if p['ntok'] or any(e[0] == 't' for e in p['elems']):
            new = emit_tokens(p['elems'], c['elems'], indent + 4, wrap, rows)
            if new is None: continue
        else:
            new = emit(build_text(p['text'], c['text'], wrap, rows), indent + 4)
        if p['cname'] and c['cname']:
            pn = ast.literal_eval(psp_t[p['cname'][0]:p['cname'][1]]); cn_ = ast.literal_eval(pc_t[c['cname'][0]:c['cname'][1]])
            if pn and cn_ and any(ord(ch) > 127 for ch in pn) and all(ord(ch) < 128 for ch in cn_):
                edits.append((p['cname'][0], p['cname'][1], lit(cn_)))
        edits.append((a, b, ' ' + new if psp_t[a] == ' ' else new))
        if p['kind'] == 'NpcTalk' and c['name'] and p['name'] is not None:
            a1, b1 = p['args'][1]
            edits.append((a1, b1, (' ' if psp_t[a1] == ' ' else '') + lit(clean(c['name']))))
    out = psp_t
    for a, b, s in sorted(edits, reverse=True):
        # keep leading whitespace of original arg
        lead = out[a:b][:len(out[a:b]) - len(out[a:b].lstrip())]
        out = out[:a] + lead + s.lstrip(' ') + out[b:]
    out = port_menus(out, pc_t)
    return out, len(ps_calls), len(pc_calls), len(pairs)


def main():
    args = [a for a in sys.argv[1:]]
    wrap, rows = 50, 3
    if '--wrap' in args: i = args.index('--wrap'); wrap = int(args[i + 1]); del args[i:i + 2]
    if '--rows' in args: i = args.index('--rows'); rows = int(args[i + 1]); del args[i:i + 2]
    psp_d, pc_d, out_d = args[:3]; only = [x.upper() for x in args[3:]]
    os.makedirs(out_d, exist_ok=True)
    rep = []
    for fn in sorted(os.listdir(psp_d)):
        if not fn.endswith('.py'): continue
        sc = fn[:-3]
        if only and sc.upper() not in only: continue
        pcp = os.path.join(pc_d, fn)
        if not os.path.exists(pcp): continue
        pt = open(os.path.join(psp_d, fn), encoding='cp932', errors='strict').read()
        ct = open(pcp, encoding='cp932', errors='replace').read()
        try:
            new, na, nb, npair = align(pt, ct, wrap, rows)
            new = new.encode('cp932', 'replace').decode('cp932')
            open(os.path.join(out_d, fn), 'w', encoding='cp932', newline='').write(new)
            rep.append('%s psp_calls=%d pc_calls=%d paired=%d' % (sc, na, nb, npair))
        except Exception as e:
            rep.append('%s ERROR %r' % (sc, e))
    open(os.path.join(out_d, '_report.txt'), 'w').write('\n'.join(rep))
    print('\n'.join(rep[:5]), '\n...', len(rep), 'scenes')


if __name__ == '__main__':
    main()
