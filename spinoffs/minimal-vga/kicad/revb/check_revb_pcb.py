#!/usr/bin/env python3
"""Content-check a generated rev B card PCB (TD.7.3, generalized for TD.9+).
  KICAD_PYTHON check_revb_pcb.py <card>
pcbnew emits UUIDs so byte-diff is meaningless (D1.25); this verifies outline size,
every board.json ref placed, the bus connector on the bottom edge, and the silk.
Skips if pcbnew is unavailable.
"""
import json, os, sys
try:
    import pcbnew
except Exception:
    print("  SKIP  PCB content check: pcbnew not importable"); sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from revb_place import BOARD_H_BY_CARD  # noqa: E402
from revb_assembly import expanded_parts, marking_text  # noqa: E402

CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
if CARD not in BOARD_H_BY_CARD:
    print(f"PCB content check FAILED:\n- unsupported card {CARD!r}")
    sys.exit(1)
BOARD_H = BOARD_H_BY_CARD[CARD]
BOARD_W, TOL = 100.0, 0.4
PCB = os.environ.get("REVB_PCB", os.path.join(
    REPO, "fab", "minimal-vga", "revb", f"{CARD}.kicad_pcb"))
STYLE = json.load(open(os.path.join(HERE, "silkscreen-style.json")))

fail = []
if not os.path.isfile(PCB):
    print(f"{CARD} PCB content check FAILED:\n- missing {PCB}"); sys.exit(1)
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}

bb = b.GetBoardEdgesBoundingBox()
w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
if abs(w - BOARD_W) > TOL or abs(h - BOARD_H) > TOL:
    fail.append(f"outline {w:.2f}x{h:.2f} != {BOARD_W}x{BOARD_H} (+-{TOL})")

spec = json.load(open(os.path.join(HERE, f"{CARD}.board.json")))
expected = set()
for c in spec["chips"]:
    if c["type"] == "REVB_BUS_39_10":
        if c["ref"] == "J_BUS":
            expected |= {"J_BUS", "J_EXT"}
        else:
            expected |= {f"{c['ref']}_BUS", f"{c['ref']}_EXT"}
    else:
        expected.add(c["ref"])
missing = expected - set(fps)
if missing:
    fail.append(f"refs not placed: {sorted(missing)}")

if "J_BUS" in fps:
    y = pcbnew.ToMM(fps["J_BUS"].GetPosition().y)
    if y < BOARD_H * 0.75:
        fail.append(f"J_BUS at y={y:.1f} not on the bottom edge")

board_texts = [d for d in b.GetDrawings()
               if isinstance(d, pcbnew.PCB_TEXT) and d.IsVisible()
               and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
footprint_texts = [d for fp in b.GetFootprints() for d in fp.GraphicalItems()
                   if isinstance(d, pcbnew.PCB_TEXT) and d.IsVisible()
                   and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
silk_texts = board_texts + footprint_texts
txt = "\n".join(d.GetText() for d in board_texts)
silk_required = ((STYLE["titles"][CARD], STYLE["common_safety_text"],
                  "SLOT 1", "SLOT 2", "SLOT 3", "SLOT 4 - KEEP EMPTY",
                  "SLOT 5 - VIDEO", "TTL ONLY", "NOT RS-232", "1:5V SENSE",
                  "2:TX 3:RX 4:GND")
                 if CARD == "backplane" else
                 (STYLE["titles"][CARD], STYLE["common_safety_text"], "PIN 1 >"))
for need in silk_required:
    if need not in txt:
        fail.append(f"silk missing {need!r}")

# Every printable text item, including footprint-owned polarity letters and the VGA
# pin-1 numeral, must use the same GOST face. This prevents a mixed KiCad-stroke /
# outline-font result from slipping through an otherwise clean render.
for item in silk_texts:
    if item.GetFontName() != STYLE["font_family"]:
        fail.append(f"silk {item.GetText()!r} font {item.GetFontName()!r} != "
                    f"{STYLE['font_family']!r}")
    if pcbnew.ToMM(item.GetTextHeight()) + 1e-6 < STYLE["minimum_text_height_mm"]:
        fail.append(f"silk {item.GetText()!r} height below style floor")

# Common title/safety hierarchy is exact on every design.
by_text = {}
for item in board_texts:
    by_text.setdefault(item.GetText(), []).append(item)
for label, expected_h in ((STYLE["titles"][CARD], STYLE["board_title_height_mm"]),
                          (STYLE["common_safety_text"], STYLE["safety_text_height_mm"])):
    matches = by_text.get(label, [])
    if len(matches) != 1:
        fail.append(f"silk {label!r} occurs {len(matches)} times, expected once")
    elif abs(pcbnew.ToMM(matches[0].GetTextHeight()) - expected_h) > 1e-6:
        fail.append(f"silk {label!r} has inconsistent text height")

# Every physical footprint has one exact reference + fitted value/role label on
# its assembly side. Whitespace is normalized so a compact multiline rendering
# and a one-line contract spelling compare identically.
def normalized(text):
    return " ".join(text.split())


by_normalized = {}
for item in board_texts:
    by_normalized.setdefault(normalized(item.GetText()), []).append(item)
assembly_parts = expanded_parts(spec)
for ref, part in sorted(assembly_parts.items()):
    label = normalized(marking_text(ref, part))
    matches = by_normalized.get(label, [])
    if len(matches) != 1:
        fail.append(f"assembly silk label {label!r} occurs {len(matches)} times, expected once")
        continue
    expected_layer = pcbnew.B_SilkS if fps[ref].GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
    if matches[0].GetLayer() != expected_layer:
        fail.append(f"assembly silk label {label!r} is not on its component side")
    if abs(pcbnew.ToMM(matches[0].GetTextHeight())
           - STYLE["assembly_text_height_mm"]) > 1e-6:
        fail.append(f"assembly silk label {label!r} has inconsistent text height")

if CARD != "backplane":
    front_pin1 = by_text.get("PIN 1 >", [])
    back_pin1 = by_text.get("< PIN 1", [])
    if len(front_pin1) != 1 or front_pin1[0].GetLayer() != pcbnew.F_SilkS:
        fail.append("front PIN 1 cue must point right toward card-bus pad 1")
    if len(back_pin1) != 1 or back_pin1[0].GetLayer() != pcbnew.B_SilkS:
        fail.append("bottom PIN 1 cue must point left toward mirrored card-bus pad 1")
else:
    reset_cue = by_text.get("U_RST TOP 1:RST 2:5V 3:GND", [])
    if len(reset_cue) != 1 or reset_cue[0].GetLayer() != pcbnew.B_SilkS:
        fail.append("backplane bottom silk must carry the U_RST service pinout")

if fail:
    print(f"{CARD} PCB content check FAILED:")
    for f in fail:
        print(f"- {f}")
    sys.exit(1)
print(f"{CARD} PCB content check OK: {w:.1f}x{h:.1f} mm, {len(fps)} footprints placed, "
      f"{len(silk_texts)} GOST silk labels present.")
