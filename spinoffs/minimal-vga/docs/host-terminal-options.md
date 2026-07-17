# VJUGA host I/O & display options (terminal / screen-scrape)

Notes on giving a minimal VJUGA (Z80) I/O without native video hardware — a host
device bridges display + keyboard to modern gear. Discussion-level, no decision made.

## Facts
- VJUGA CPU is **Z80** (single +5V rail, built-in refresh, simple bus). Use **SRAM**,
  not DRAM → no refresh/RAS-CAS at all. Z80 runs 8080 code, so most of the Juku ROM
  is reusable; only the console/peripheral layer changes.
- Framebuffer: **9640 bytes at `0xD800`** (40×241, ~320×240 mono bitmap). It is a
  *bitmap*, not a text buffer — scraping = pixels. Check the memory map for a smaller
  character array before committing to the pixel path.

## Two I/O approaches
- **A — serial console in firmware (easiest).** `CONIN`/`CONOUT` against a UART
  (КР580ВВ51 / 8251), host = dumb USB-serial bridge. ~few hundred bytes of asm.
  RC2014 / Grant Searle path.
- **B — scrape video RAM (no firmware change).** Host reads the framebuffer via bus
  DMA (BUSREQ/BUSACK) and injects keys. Zero ROM change, but needs bus arbitration +
  keyboard-matrix injection. More hardware.

## Full-frame scrape bandwidth (Approach B over serial)
`fps = baud / (10 × 9640)` → ~1.2 fps @115200, ~10 fps @1M, ~20 fps @2M.
- Arduino Uno's **2 KB SRAM can't hold a 9.6 KB frame** → stream-while-bus-held (stalls
  Z80) or chunk. Reading the RAM itself is fast (~10 ms via direct port I/O).
- **Fix: send deltas, not frames.** Dirty `(addr,byte)` pairs / dirty 256-byte blocks →
  typing feels instant; only scroll/clear pays a full-frame cost. RLE helps (mostly blank).

## Host device comparison
| Host | 5V bus | Determinism | HDMI/display |
|---|---|---|---|
| **Arduino Uno** | **native 5V, no shifter** | fine for bus DMA | none; USB-serial to PC. 2 KB RAM is the limiter |
| **Original Pi (bare-metal)** | 3.3V, **needs level shifters** | tight bare-metal loop | **yes** — GPU boots first, HDMI = mailbox→framebuffer→write pixels; ~10 ms/frame read → 30–60 fps full frames. No OS needed |
| **BeagleBone** | 3.3V, needs shifters (**ADC is 1.8V!**) | **PRU = best** (200 MHz cycle-accurate GPIO) | **Black: micro-HDMI; White: none** |

## Key takeaways
- **3.3V boards (Pi, BeagleBone) need level shifters on the 5V bus; Arduino Uno is the
  only 5V-native option.** This is the one constant.
- **Bare-metal Pi deletes the serial-bandwidth problem** — no UART in the middle, Pi reads
  RAM directly and blits to HDMI. HDMI is a GPU mailbox call, not signal-banging. USB
  keyboard is the hard part (use PS/2/matrix/UART, or the **Circle** framework which
  provides USB). Ref: Baking Pi (Pi 1 / ARMv6), Circle, dwelch67.
- **BeagleBone Black** is the strongest all-in-one: **PRU** for cycle-accurate bus reads +
  micro-HDMI for display, ARM gluing via shared memory. (White has no HDMI.)
- No OS/RTOS is required on the Pi/BBB — a bare-metal loop suffices. If wanted for the Pi:
  Ultibo, Circle, RTEMS, FreeRTOS, or PREEMPT_RT Linux (soft-RT). Zephyr does **not**
  support the original Pi's ARM11.
