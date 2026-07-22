#!/bin/sh
# Regenerate the board preview PNGs in renders/ from the routed board.
# Run after any change to kicad/juku_routed.kicad_pcb (the pre-commit hook in
# .githooks/ does this automatically when the board is staged).
#
# Works with both KiCad 9 and KiCad 10:
#   * 3D views use `pcb render`, present in both.
#   * 2D copper+silk views use `pcb export png` on KiCad 9. KiCad 10 dropped the
#     png exporter, so there we plot to SVG and rasterize with rsvg-convert
#     (which renders KiCad's embedded silkscreen glyphs cleanly).
# Silk text is re-rendered from the installed "GOST CAD KK" font (fonts/gost.ttf,
# Cyrillic-capable); install that font on the render host or the Cyrillic chip
# values render as tofu boxes. See fonts/README.md.
set -e
cd "$(dirname "$0")/.."
KCLI="$(scripts/find-kicad-cli.sh)"
BOARD="${1:-kicad/juku_routed.kicad_pcb}"
mkdir -p renders

# Preview resolution. Bump these to trade file size for detail.
DPI_2D=600          # KiCad 9 raster png export
WIDTH_2D=6000       # KiCad 10 SVG-fallback raster width (px)
WIDTH_3D=3000       # 3D raytrace width (px); heights keep the framing aspect
HEIGHT_3D_TOP=2574
HEIGHT_3D_PERSP=2145

# Does this kicad-cli still ship the raster png exporter? (KiCad 9 yes, 10 no.)
if "$KCLI" pcb export --help 2>&1 | grep -qw png; then
  HAVE_PNG_EXPORT=1
else
  HAVE_PNG_EXPORT=0
  command -v rsvg-convert >/dev/null 2>&1 || {
    echo "This kicad-cli has no png exporter; need rsvg-convert to rasterize the" >&2
    echo "2D SVG fallback (brew install librsvg / apt install librsvg2-bin)." >&2
    exit 3
  }
fi

# 2D copper + silk, one side at a time. front = component side (F.*),
# back = solder side (B.*, mirrored so it reads as viewed from the back).
render_2d() {
  side="$1"
  if [ "$side" = front ]; then
    cu=F.Cu; silk=F.SilkS; mirror=
  else
    cu=B.Cu; silk=B.SilkS; mirror=--mirror
  fi
  out="renders/board_2d_$side.png"
  if [ "$HAVE_PNG_EXPORT" = 1 ]; then
    tmp="$(mktemp -d "${TMPDIR:-/tmp}/juku_png_XXXXXX")"
    # shellcheck disable=SC2086
    "$KCLI" pcb export png --layers "$cu" --common-layers "$silk",Edge.Cuts $mirror \
        --scale 0 --dpi "$DPI_2D" -o "$tmp" "$BOARD" >/dev/null 2>&1
    mv "$tmp"/*.png "$out"
    rm -rf "$tmp"
  else
    # KiCad 10: plot copper+edge and silk to separate SVGs, then draw silk on
    # top. A single combined plot paints copper over the silk (labels vanish),
    # so we merge the silk plot's body after the copper plot's and rasterize
    # once with rsvg-convert (which renders KiCad's Cyrillic glyphs cleanly).
    cusvg="$(mktemp "${TMPDIR:-/tmp}/juku_cu_XXXXXX.svg")"
    sksvg="$(mktemp "${TMPDIR:-/tmp}/juku_sk_XXXXXX.svg")"
    # shellcheck disable=SC2086
    "$KCLI" pcb export svg --layers "$cu",Edge.Cuts $mirror \
        --page-size-mode 2 --fit-page-to-board --exclude-drawing-sheet --mode-single \
        --output "$cusvg" "$BOARD" >/dev/null 2>&1
    # shellcheck disable=SC2086
    "$KCLI" pcb export svg --layers "$silk" $mirror \
        --page-size-mode 2 --fit-page-to-board --exclude-drawing-sheet --mode-single \
        --output "$sksvg" "$BOARD" >/dev/null 2>&1
    merged="$(mktemp "${TMPDIR:-/tmp}/juku_merged_XXXXXX.svg")"
    python3 - "$cusvg" "$sksvg" "$merged" <<'PY'
import re, sys
cu = open(sys.argv[1]).read()
silk = open(sys.argv[2]).read()
body = silk[re.search(r'<svg\b[^>]*>', silk).end():silk.rfind('</svg>')]
open(sys.argv[3], 'w').write(cu[:cu.rfind('</svg>')] + body + '</svg>\n')
PY
    # Black background to match the KiCad 9 png style (copper on black).
    rsvg-convert --background-color=black -w "$WIDTH_2D" "$merged" -o "$out"
    rm -f "$cusvg" "$sksvg" "$merged"
  fi
}

render_2d front
render_2d back

"$KCLI" pcb render --side top --quality high --width "$WIDTH_3D" --height "$HEIGHT_3D_TOP" \
    --background opaque -o renders/board_3d_top.png "$BOARD" >/dev/null 2>&1
"$KCLI" pcb render --rotate "-30,20,-20" --zoom 0.9 --quality high --width "$WIDTH_3D" --height "$HEIGHT_3D_PERSP" \
    --background opaque -o renders/board_3d_persp.png "$BOARD" >/dev/null 2>&1
echo "renders/ updated: $(ls renders/*.png | wc -l | tr -d ' ') views"
