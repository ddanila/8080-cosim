# T31 physical validation on CS00015

Date: 2026-08-03  
Board: Arvutimuuseum Juku processor board `CS00015`  
ROM socket: D15, AT28C64B; D16 unpopulated  
Serial: X3 through MAX3232 and CP2102, 2400 baud

## Image

- DOS name: `T31HOST.BIN`
- ROM version: `1Ah`
- Self-CRC16: `72EF`
- SHA-256: `a4fed9185616bbfbef22ab6f0b18202e6d79ad7dbe3b7c46a77a700d3af3676c`
- Executed monitor boundary: loader ends at `0FFFh`

## Cold-boot probe

The ROM produced one happy beep and did not enter the T30 restart cycle. The
host decoded the exact `1A/72EF` banner, completed the adaptive handshake with
zero mismatches, and reported:

- PIC: PASS
- PPI: PASS
- D54: PASS
- D55: FAIL (the independently known CS00015 fault)
- D57: PASS
- RAM `4000h-4FFFh`: PASS
- RAM `C000h-CFFFh`: PASS
- loader API v2: READY at `0A00h`, maximum chunk 32 bytes
- T28-compatible control PROBE: complete, RAM unchanged

Evidence: `jukuravi-logs-t31-real/20260803T150916.115911Z.json`.

## Resident attach, upload, and CALL/RET

After the first host exited, a new host process attached to the still-running
loader without RESET. It uploaded the 29-byte `return-4000.bin` to `4000h` in
one transaction, obtained exact readback, called it, and received:

- RUN acknowledged, one attempt
- returned A: `42h`
- RETURN replays: 0
- result RAM at `4100h`: `54 32 38 52 45 54 21 00` (`T28RET!\0`)
- result read attempts: 1
- final host status: `ok`

Evidence: `jukuravi-logs-t31-call/20260803T151046.564402Z.json`.

This proves the required operating model on real hardware: a host can attach
without reset, upload arbitrary 8080 bytes, execute a cooperative snippet by
CALL, receive A and a RAM result block after ordinary RET, and keep the ROM
monitor resident for subsequent work.
