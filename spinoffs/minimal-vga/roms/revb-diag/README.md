# DIAG/VJUGA

`build_diag.py` emits the 16 KiB diagnostic member used in the rev-B ROM set.
Its reset path emits POST directly and does not establish a stack or call a
helper until ROM integrity, RAM data and RAM address tests pass. It then tests
D57, emits a tone, initializes the real 8251, configures PPI/PIC, writes a
visible framebuffer stripe, and finishes at retained code `FFh` with TTL detail.

The RAM tests write and verify fixed `A5h`/`5Ah` patterns, then each location's
low address byte, over `4000h–D6FFh`. The address pattern does not distinguish
aliases with the same low byte; a PASS does not prove every address line.

Rebuild the complete programming set from the repository root:

```sh
python3 spinoffs/minimal-vga/roms/build_revb_rom.py
```

Check image freshness, early stack use, and ordered POST execution in cosim
(requires a C compiler and the POSIX PTY support used by the C oracle):

```sh
python3 spinoffs/minimal-vga/roms/check_revb_rom_set.py
```

The ROM checks D57 count readback and initialized USART status. PPI/PIC
configuration writes and the framebuffer pattern do not independently test
those peripherals or prove a physical display or audible tone. The gate checks the generated instruction map for early `LXI SP`, `CALL`,
`PUSH` and `POP`, then executes a 20-million-cycle C-oracle run. It requires the
16-code POST sequence, selected D57 count/latch and tone writes, four late serial
phrases, and exactly 40 framebuffer writes before `FFh`. It does not compare the
written framebuffer bytes or render a display. Its negative controls inject an
early CALL and swap two POST codes.

The checker runs the oracle from `cosim/` and overwrites its scratch `vram.bin`;
save any framebuffer you need before running it. These are modeled instruction
and I/O checks; assembled-board acceptance remains separate.
