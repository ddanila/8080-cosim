#!/usr/bin/env python3
"""Mark unpopulated sockets as such on an already-built .kicad_pcb.

The generator (gen_kicad_pcb.py) does this for a fresh board, but the promoted
routed board and the source board are hand-maintained and not regenerated, so
this applies the same population intent to them directly, driven by the model
(`populated: false` in kicad/juku.board.json) so the ref list is never
hardcoded. For every unpopulated socket it:

  * hides the chip Value text (so the silk/preview shows an empty socket --
    outline + refdes -- instead of a phantom К573РФ5 / 565РУ3Г marking), and
  * flags the footprint DNP + excluded from position files.

Pure text surgery (paren-aware) so the diff stays minimal and the stripped
render_cache is not regenerated. Idempotent. Run: apply_socket_population.py
kicad/juku_routed.kicad_pcb [more boards...]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def unpopulated_refs():
    d = json.loads((ROOT / "kicad" / "juku.board.json").read_text(encoding="utf-8"))
    return {c["ref"] for c in d["chips"] if c.get("populated") is False}


def balanced(s, start):
    """End index (exclusive) of the s-expression that opens at s[start]=='('."""
    depth = 0
    for k in range(start, len(s)):
        if s[k] == "(":
            depth += 1
        elif s[k] == ")":
            depth -= 1
            if depth == 0:
                return k + 1
    raise ValueError("unbalanced")


def footprint_spans(s):
    spans = []
    idx = 0
    while True:
        j = s.find("\t(footprint ", idx)
        if j < 0:
            break
        end = balanced(s, j + 1)
        spans.append((j + 1, end))
        idx = end
    return spans


def hide_value(block):
    """Add (hide yes) to the footprint's own Value property if absent."""
    m = re.search(r'\(property "Value" "', block)
    if not m:
        return block, False
    pstart = m.start()
    pend = balanced(block, pstart)
    prop = block[pstart:pend]
    if "(hide yes)" in prop:
        return block, False
    lm = re.search(r'(\n(\s*)\(layer "[^"]*"\))', prop)
    if not lm:
        return block, False
    indent = lm.group(2)
    new_prop = prop[:lm.end()] + f"\n{indent}(hide yes)" + prop[lm.end():]
    return block[:pstart] + new_prop + block[pend:], True


def mark_dnp(block):
    m = re.search(r'\(attr ([^)]*)\)', block)
    if not m:
        return block, False
    toks = m.group(1).split()
    added = False
    for t in ("dnp", "exclude_from_pos_files"):
        if t not in toks:
            toks.append(t)
            added = True
    if not added:
        return block, False
    return block[:m.start()] + f"(attr {' '.join(toks)})" + block[m.end():], True


def patch(path, refs):
    s = Path(path).read_text(encoding="utf-8")
    changed = []
    # Walk spans back-to-front so edits don't shift earlier offsets.
    for start, end in reversed(footprint_spans(s)):
        block = s[start:end]
        rm = re.search(r'\(property "Reference" "([^"]*)"', block)
        if not rm or rm.group(1) not in refs:
            continue
        ref = rm.group(1)
        block, h = hide_value(block)
        block, d = mark_dnp(block)
        if h or d:
            s = s[:start] + block + s[end:]
            changed.append(ref)
    Path(path).write_text(s, encoding="utf-8")
    return sorted(changed)


def main():
    refs = unpopulated_refs()
    targets = sys.argv[1:] or ["kicad/juku_routed.kicad_pcb"]
    for t in targets:
        changed = patch(t, refs)
        print(f"{t}: marked {len(changed)} unpopulated socket(s) DNP + value-hidden")


if __name__ == "__main__":
    main()
