# Fonts

Project-local fonts used by generated fabrication artifacts.

- `gost.ttf` - GOST CAD font, resolved by KiCad/fontconfig as family
  `GOST CAD KK`. The production silkscreen face includes the Cyrillic glyphs
  required by replica chip values such as `К573РФ5` / `КР580ВА86`. Also used
  by `kicad/validate_placement.py` for placement overlays.
- `gost-type-b-italic.ttf` - GOST 2.304-81 type B italic font. Its internal
  family/style names are normalized so KiCad/fontconfig resolves it as
  `GOST type B italic` / `Regular`. **It has no Cyrillic glyphs** and must not
  be used for the replica silkscreen. Kept only for Latin-only artifacts.

KiCad needs the `GOST CAD KK` face installed to render/edit the main replica's
silkscreen (install `gost.ttf` into a system/user font directory and refresh the
font cache; `kicad-cli` re-renders text from the installed font). VJUGA Rev B uses the same `GOST CAD KK` family in Book style for all five
boards, as pinned in
[its silkscreen contract](../spinoffs/minimal-vga/kicad/revb/silkscreen-style.json).
See [the Rev B audit](../spinoffs/minimal-vga/docs/rev-b-silkscreen-audit.md)
for text dimensions and coverage checks.
Gerber exports contain vector geometry and do not require the font at upload
or during fabrication.

`kicad/check_silk_glyphs.py` guards the replica silk against missing-glyph
regressions: it verifies every character used in silk text is present in the
referenced face's font file.
