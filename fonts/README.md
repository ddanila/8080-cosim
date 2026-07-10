# Fonts

Project-local fonts used by generated fabrication artifacts.

- `gost.ttf` - GOST CAD font used by `kicad/validate_placement.py` for placement
  overlays; it is not the production silkscreen face.
- `gost-type-b-italic.ttf` - GOST 2.304-81 type B italic font used by generated
  artifacts that explicitly need italic text. Its internal family/style names are
  normalized so KiCad/fontconfig resolves it as `GOST type B italic` /
  `Regular`.

KiCad needs the italic face available to render/edit the main replica's
silkscreen. The VJUGA generator deliberately uses KiCad's default stroke text
so its labels match footprint reference/value text.
