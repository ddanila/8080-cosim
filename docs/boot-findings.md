# Boot findings — ekta43.bin (RomBios 2.43m, EktaSoft, AT-keyboard homebrew #0043)

Empirical results from `cosim/trace.c` (traced superzazu 8080, MIT) plus the
authoritative map from MAME (see `hardware-map.md`).

## Confirmed / resolved
- ROM 16 KB at `0x0000`; reset `JMP 0x0017` → signature NOPs → `JMP 0x01A8` (init).
- Full I/O port map recovered and matches the chip inventory (see hardware-map.md).
- Memory **banking** modelled: 4-mode view via 8255#0 Port C bits[1:0]
  (`trace.c` handles direct Port C writes on port `0x06` and 8255 BSR on `0x07`).
- Video framebuffer located: DRAM `0xD800`, stride 40 (320 px), MSB-first.
- Init at `0x01A8` is correct: configures both 8255s, sets stack `0xD450`,
  does a warm-boot RAM-signature probe, programs all three 8253 PITs.
- The earlier "comb" render was the `0x55` RAM-test pattern; the `0x00CE`
  `OUT 0x07 / JMP 0x00D2` is the real error trap and we never hit it.

## The wall (current)
Boot **never reaches the banner**. Even at 3e9 cycles (~25 min of CPU time):
`mode=0`, zero bank switches, **nothing ever written to the `0xD8xx` video region**.
It is in an **infinite retry loop**:

```
0442/0443: strobe sequence    ; sub 0x046B = read Port A latch / set low nibble / pulse bit7 strobe
0444..0468: program PIT#2 + two big software delays (CALL 0x047B), loop C times
0042D..0442: checksum/sum a memory block (ADD M / INX H / DCX D ...)
```

i.e. **strobe-something → wait → read-back/checksum → doesn't match → retry forever.**
`iff=0` throughout and the only polled input is 8255#0 Port A readback.

### Diagnosis
It is waiting on an **external peripheral handshake that we don't model** — almost
certainly the **AT keyboard / key-encoder** (this BIOS is the AT-keyboard homebrew
variant; the Port A strobe drives the keyboard side, the checksum reads its
response). MAME models a key-encoder device and boots fine.

## Options to get past it (decision pending)
1. **Model the key-encoder/AT-keyboard handshake** in our harness (study MAME's
   key-encoder device + the 8255#0 Port A/B protocol, feed the expected
   self-test/response). Most faithful; most work.
2. **Use MAME as the golden behavioral reference** for the banner/boot, and keep
   our custom harness for the parts the PCB co-sim/LVS actually needs.
3. **Reassess scope**: the LVS/connectivity-sync goal may not require a full
   behavioral boot at all — the authoritative map in `hardware-map.md` may already
   be enough to drive the KiCad↔HDL work.

## Tooling built
- `cosim/trace.c`   — traced 8080 with faithful Juku banking + instrumentation
- `cosim/dis8080.py`— full 8080 disassembler (used to recover the boot flow)
- `cosim/render.py` — render a raw mono framebuffer dump to PNG
- `cosim/i8080.*`   — vendored MIT 8080 core
- `ref/mame_juku.cpp` — MAME driver (BSD-3), the hardware ground truth
