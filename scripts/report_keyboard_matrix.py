#!/usr/bin/env python3
"""Guard and report the factory ДГШ5.104.015 Э3 keyboard matrix."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = {
    "PXL_20260718_122207428.jpg": "0f1181da026921a845682d6d8946838dc9d8ad88cec1e6c4d2f8e6a4de3b1b15",
    "PXL_20260718_122210592.jpg": "e332401bd2244d94e81c851e37a38a7fb5f1d65660c0be577cce9bd0ee1a9ff6",
    "PXL_20260718_122213927.jpg": "658c00c054c85017f6dbfcbf732e561aedc395c9faa345f76adfff35eef63a17",
}

# (unshifted, shifted) at each factory scan line.  None means no fitted key in
# that encoder row.  National legends are retained literally from the drawing;
# slash-separated text denotes two legends on one key, not two switch contacts.
MATRIX = {
    0: (("F6", None), ("N", None), None, ("Y", None), ("6", "&"), ("H", None)),
    1: (None, ("X", None), None, ("W", None), ("2", '"'), ("S", None)),
    2: (("F4", None), ("V", None), None, ("R", None), ("4", "$"), ("F", None)),
    3: (("F1", None), None, None, ("TAB", None), ("ESC", None), ("CAPS LOCK", None)),
    4: (("F5", None), ("B", None), None, ("T", None), ("5", "%"), ("G", None)),
    5: (("F2", None), ("Z", None), None, ("Q", None), ("1", "!"), ("A", None)),
    6: (("F3", None), ("C", None), None, ("E", None), ("3", "#"), ("D", None)),
    7: (("F7", None), ("M", None), None, ("U", None), ("7", "'"), ("J", None)),
    8: (None, None, ("DEL", None), ("] / õ", None), ("ERASE", None), ("RETURN", None)),
    9: (None, None, ("↓", None), ("[ / ö", None), ("Ä / Ü", None), None),
    10: (None, None, ("↑", None), ("õ / Õ", None), ("Ö / Õ", None), (":", "*")),
    11: (None, (";", "+"), ("SPACE", None), ("\\ / ^", None), ("-", "="), ("ä / Ä", None)),
    12: (None, ("/", "?"), ("→", None), ("P", None), ("0", "_"), ("ö / Ö", None)),
    13: (None, (".", ">"), ("← / BACKSPACE", None), ("O", None), ("9", ")"), ("L", None)),
    14: (("F8", None), (",", "<"), ("LAT/RUS", None), ("I", None), ("8", "("), ("K", None)),
}
# ASCII injection contract: character -> (column, 74148 input bit, shift).
EXPECTED = {}
for ch, col, bit in [
    ("a",5,5),("b",4,1),("c",6,1),("d",6,5),("e",6,3),("f",2,5),("g",4,5),("h",0,5),
    ("i",14,3),("j",7,5),("k",14,5),("l",13,5),("m",7,1),("n",0,1),("o",13,3),("p",12,3),
    ("q",5,3),("r",2,3),("s",1,5),("t",4,3),("u",7,3),("v",2,1),("w",1,3),("x",1,1),
    ("y",0,3),("z",5,1),
]: EXPECTED[ch] = (col, bit, 0)
for ch, col in zip("0123456789", (12,5,1,6,2,4,0,7,14,13)): EXPECTED[ch] = (col, 4, 0)
for ch, col in zip('!"#$%&\'()_', (5,1,6,2,4,0,7,14,13,12)): EXPECTED[ch] = (col, 4, 1)
EXPECTED.update({
    " ":(11,2,0), "\r":(8,5,0), "\n":(8,5,0), "\t":(3,3,0), "\b":(13,2,0), "\x1b":(3,4,0),
    ".":(13,1,0), ">":(13,1,1), ",":(14,1,0), "<":(14,1,1), "/":(12,1,0), "?":(12,1,1),
    ";":(11,1,0), "+":(11,1,1), "-":(11,4,0), "=":(11,4,1), ":":(10,5,0), "*":(10,5,1),
    "[":(9,3,0), "]":(8,3,0), "\\":(11,3,0), "^":(11,3,1),
})
SYNTHETIC_EXPECTED = {
    0x80: (9, 2, 0),    # Down
    0x81: (8, 4, 0),    # Erase
    0x82: (4, 0, 0),    # F5
    0x83: (0, 0, 0),    # F6
    0x84: (14, 0, 0),   # F8
    0x86: (14, 0, 1),   # Shift-F8
    0x87: (3, 0, 0),    # F1
    0x88: (5, 0, 0),    # F2
    0x89: (6, 0, 0),    # F3
    0x8A: (2, 0, 0),    # F4
    0x8B: (10, 2, 0),   # Up
    0x8C: (12, 2, 0),   # Right
    0x8D: (13, 2, 0),   # Left
    0x8F: (10, 2, 1),   # Shift-Up
    0x90: (9, 2, 1),    # Shift-Down
    0x91: (7, 0, 0),    # F7
}

CHAR_RE = re.compile(r"\{'((?:\\[0-7]{3}|\\.|[^']))',\s*(\d+),(\d+),(\d+)\}")
HEX_CHAR_RE = re.compile(
    r"\{'\\x([0-9a-fA-F]{2})',\s*(\d+),(\d+),(\d+)\}",
)

def decode_c_char(token: str) -> str:
    if token == r"\033": return "\x1b"
    return bytes(token, "ascii").decode("unicode_escape")

def main() -> None:
    photo_dir = ROOT / "ref/photos/dgsh5-104-015-e3"
    for name, expected in PHOTOS.items():
        actual = hashlib.sha256((photo_dir / name).read_bytes()).hexdigest()
        if actual != expected: raise SystemExit(f"photo hash mismatch: {name}")

    source = (ROOT / "cosim/trace.c").read_text()
    actual = {decode_c_char(c): (int(col), int(bit), int(shift)) for c, col, bit, shift in CHAR_RE.findall(source)}
    if actual != EXPECTED:
        missing = sorted(set(EXPECTED) - set(actual))
        extra = sorted(set(actual) - set(EXPECTED))
        wrong = sorted(k for k in EXPECTED.keys() & actual.keys() if EXPECTED[k] != actual[k])
        raise SystemExit(f"cosim KMAP mismatch: missing={missing!r} extra={extra!r} wrong={wrong!r}")
    actual_synthetic = {
        int(value, 16): (int(col), int(bit), int(shift))
        for value, col, bit, shift in HEX_CHAR_RE.findall(source)
    }
    if actual_synthetic != SYNTHETIC_EXPECTED:
        raise SystemExit(
            "cosim synthetic KMAP mismatch: "
            f"expected={SYNTHETIC_EXPECTED!r} actual={actual_synthetic!r}"
        )

    def cell(item):
        if item is None: return "—"
        lo, hi = item
        return lo if hi is None else f"{lo} / {hi}"

    rows = []
    for col, keys in MATRIX.items():
        rows.append(f"| {col + 1} | {col} | " + " | ".join(cell(x) for x in keys) + " |")
    report = """# Factory keyboard matrix — `ДГШ5.104.015 Э3`

Generated from the retained transcription in `scripts/report_keyboard_matrix.py`.
The generator verifies the three source-photo hashes and compares cosim source
mapping tuples with its expected tuples. It does not reread the photographs,
simulate the HDL, or verify physical keyboard continuity. The transcription is
an electrical coordinate map; host-key placement and physical fit need separate
checks.

Regenerate with `python3 scripts/report_keyboard_matrix.py`.
`sync/keyboard_matrix_check.sh` also requires the generated report to match the
tracked copy.

## Coordinate result

The drawing numbers its fifteen decoder outputs 1–15; software therefore writes
factory line minus one to PPI D26 Port A bits PA0–PA3 (`SC0–SC3`).  The six
horizontal buses are deliberately not binary ordered: factory rows 1–6 reach
the model's 74148 input bits 4, 3, 5, 1, 0, and 2 respectively.  D1/D2 encode
those inputs onto `K0–K2`; their diode OR produces active-low `-FK`.  `SHIFT`
and `CTRL` bypass the matrix encoder and appear separately on X1.

| factory line | model column | row 5 / bit 0 | row 4 / bit 1 | row 6 / bit 2 | row 2 / bit 3 | row 1 / bit 4 | row 3 / bit 5 |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
""" + "\n".join(rows) + """

Shifted punctuation is shown after `/`.  Paired national legends separated by
`/` are literal cap legends and remain a firmware/font interpretation boundary.

## Connector X1

| pin | net | role |
| ---: | --- | --- |
| 1 | `K2` | encoded matrix row |
| 2 | `K0` | encoded matrix row |
| 3 | `K1` | encoded matrix row |
| 4 | `-FK` | active-low key-present flag |
| 5 | ground | supply return |
| 6 | `+5V` | supply |
| 7 | `SHIFT` | dedicated modifier return |
| 8 | `CTRL` | dedicated modifier return |
| 9 | `CONTRDAT` | serialized S21 configuration-switch return |
| 10 | — | no connection shown |
| 11 | `SC0` | scan-address bit |
| 12 | `SC1` | scan-address bit |
| 13 | `SC2` | scan-address bit |
| 14 | `SC3` | scan-address bit |

## Configuration switches S21

The keyboard drawing contains an eight-position `S21` bank labelled
`НАСТРОЙКА` (configuration).  During scan positions 8–15 its selected switch
returns serially on `CONTRDAT` to the mainboard E8.4 selector terminal. The
exact `.009` sheet-1 drawing sends D26 PB4/pin22 to E8.3 and PB5/pin23 to
E8.2; the `.009` assembly and owner photo show the 3–4 bridge fitted. The
replica netlist now assigns this return to PB4; its routed copper remains open
pending A50 hole identification and direct continuity.

EktaSoft 3.7 decodes the S21 bits as follows, but its archived ROM bytes at
`1211h..1216h` (`DB 05 2F FB E6 20`) mask **PB5**, not PB4. That ROM profile
and the photographed `.009` 3–4 bridge therefore disagree on the selected
input; see `docs/ekta37-netbios-notes.md`.

| switch | configuration bit | NetBios meaning |
| ---: | ---: | --- |
| S21.1 | 7 | interface: onboard D11 or expansion interface |
| S21.2–S21.3 | 6–5 | maximum station number: 3, 7, 15, or 31 |
| S21.4–S21.8 | 4–0 | this station's number |

In the EktaSoft 3.7 PB5 simulation profile, a nonzero configuration accepts
`TN` with no Enter and takes network identity from S21. A zero configuration
falls through to the ROM's `N=` and `S=` keyboard prompts; cosim deliberately
models that open-switch fallback and therefore injects `TN0201`. The same
behavior on the `.009` PB4-strapped board remains unverified.

The implemented network-first ROM uses reset-latched S21 configuration shared
with CP/M. Bits 2:1 select 40x24, 53x24, 64x20 or 80x24; bits 4:3 select
English, Estonian, CP866 Russian or English/user-remap. C4--C8 use bit 0 for
automatic boot versus local recovery wait; C9 and successors reserve it and
always boot from the network. This software policy does not resolve the
archived EktaSoft PB5 versus photographed PB4 selector boundary above.
See [the network-ROM contract](../spinoffs/jukuravi/network-rom/README.md)
and [C12 qualification](c12-runtime-console.md) for runtime overrides and
physical acceptance scope.

## Model comparison

- All 26 letters, ten digits, their drawing-visible ASCII shift pairs, Space,
  Return, Tab, Escape, Backspace/Left, and ASCII punctuation now have exact
  drawing-derived cosim tuples.  Uppercase letters assert the dedicated SHIFT
  return while reusing the lowercase matrix contact.
- The HDL accepts the same `(column, key-bit, shift)` tuple at its simulation
  boundary; shifted `T` remains column 4, bit 3 and reads as Port B `0x88`.
- No-key remains `0xCF`: `K0–K2` and `-FK` released, SHIFT/CTRL released.
- Interactive PTY bytes `80`..`91` (except `85` and `8e`) inject the guarded
  Down, Erase, F5, F6, F8, Shift-F8, F1, F2, F3, F4, Up, Right, Left,
  Shift-Up, Shift-Down, and F7 contacts. `85` and `8e` inject Ctrl-Up/Home and
  Ctrl-Down/End outside `KMAP`. These bytes are a cosim test protocol, not
  character encodings exposed to Juku software.
- `JUKU_KEY_AT_PC=PC:BYTE` begins one of those same mapped contacts at an exact
  guest instruction boundary and then applies the ordinary hold/release frame
  timing. `JUKU_KEY_AT_PC_HOLD_FRAMES` can lengthen only that one triggered
  contact across a slow guest operation without changing queued-key timing;
  `JUKU_KEY_AT_PC_GATE=ADDRESS:BYTE` can additionally require a guest-memory
  byte before the one-shot trigger is armed. It is the deterministic raw-poll
  test interface; it does not return a key value directly or bypass the
  matrix.
- The C7 ABI fixture feeds raw bytes `86` and `85` directly through this
  matrix model and requires the public raw-key vector to return column/PB
  pairs `0E/8E` and `0A/6A`. This is an executable regression for the exact
  modified contacts, not an inference from translated ASCII input.
- The matrix transcription includes contacts beyond the ASCII and synthetic
  tuple sets listed above. Those stimulus checks do not establish complete
  host-byte coverage of every locking, national or mode-switch contact.

"""
    out = ROOT / "docs/factory-keyboard-matrix.md"
    out.write_text(report.rstrip() + "\n")
    print(f"keyboard matrix: 15 scan lines, {sum(x is not None for row in MATRIX.values() for x in row)} fitted matrix positions")
    print(
        f"cosim tuples: {len(EXPECTED)} ASCII + "
        f"{len(SYNTHETIC_EXPECTED)} synthetic exact matches"
    )

if __name__ == "__main__": main()
