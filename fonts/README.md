# Fonts

Project-local fonts used by generated fabrication artifacts.

- `gost.ttf` - GOST CAD font asset kept for experiments; it is visually slanted
  and is not used by the VJUGA board silkscreen.
- `gost-type-b-italic.ttf` - GOST 2.304-81 type B italic font used by generated
  artifacts that explicitly need italic text. Its internal family/style names are
  normalized so KiCad/fontconfig resolves it as `GOST type B italic` /
  `Regular`.

KiCad still needs the font available to render/edit text interactively. The
VJUGA PCB generator uses KiCad's default stroke text for generated silkscreen
labels so those labels match footprint reference/value text.
