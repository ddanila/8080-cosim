# DIAG/VJUGA

`build_diag.py` emits the 16 KiB diagnostic member used in the rev-B ROM set.
Its reset path emits POST directly and does not establish a stack or call a
helper until ROM integrity, RAM data and RAM address tests pass. It then tests
D57, emits a tone, initializes the real 8251, configures PPI/PIC, writes a
visible framebuffer stripe, and finishes at retained code `FFh` with TTL detail.

Rebuild the complete programming set from the repository root:

```sh
python3 spinoffs/minimal-vga/roms/build_revb_rom.py
```
