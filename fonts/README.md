# Fonts

Project-local fonts used by generated fabrication artifacts.

- `gost.ttf` - existing GOST CAD font asset.
- `gost-type-b-italic.ttf` - GOST 2.304-81 type B italic font used by generated
  silkscreen labels. KiCad/fontconfig resolves it as `GOST type B italic`.

KiCad still needs the font available to render/edit text interactively. The
minimal VGA PCB generator writes the expected font face into generated
silkscreen text and the PCB checker verifies that the reference is present.
