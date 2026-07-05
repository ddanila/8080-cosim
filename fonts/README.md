# Fonts

Project-local fonts used by generated fabrication artifacts.

- `gost.ttf` - straight GOST CAD font asset used by generated silkscreen
  labels. KiCad/fontconfig resolves it as `GOST CAD KK` / `Book`.
- `gost-type-b-italic.ttf` - GOST 2.304-81 type B italic font used by generated
  artifacts that explicitly need italic text. Its internal family/style names are
  normalized so KiCad/fontconfig resolves it as `GOST type B italic` /
  `Regular`.

KiCad still needs the font available to render/edit text interactively. The
VJUGA PCB generator writes the expected font face into generated
silkscreen text and the PCB checker verifies that the reference is present.
