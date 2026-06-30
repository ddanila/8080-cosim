# Keyboard subsystem — scoping for interactive emulation

Goal: feed keystrokes so the (displaying, polled) **ekta37** BIOS *reacts to commands* at
its `*` prompt. Scoped from the cosim behaviour + MAME's `juku` driver.

## How ekta37 reads the keyboard (observed)
At idle (after the banner), ekta37 sits in a tight loop (PCs 0xD7E7–0xD7F0) **reading
8255#0 Port C (port 0x06) ~179k times**, scanning for a key; it reads Port A/B (0x04/0x05)
only when a key is present. So the keyboard is **polled**, not interrupt-driven — no frame
interrupt needed for ekta37 input.

## The hardware protocol (from MAME)
- **16 key columns** (`COL.0..COL.15`) — the full matrix is in `ref/mame_juku.cpp`
  (`PORT_START("COL.n")` + `PORT_BIT` → key/char). Active-LOW (pressed = 0).
- **74148 priority encoder** (`m_key_encoder`) — the selected column's row lines feed a
  74148 → a **3-bit row code** + **GS** ("some key in this column"). So a key = (column,
  3-bit row code).
- **SPECIAL port** = SHIFT/CTRL/etc. modifiers.
- The 8255 selects the column (SC0–3 = 4 bits → 16 cols) and reads back the 74148 result
  (row code + GS strobe) — that's the Port C read ekta37 polls.

## Implementation plan (cosim, opt-in)
1. **Matrix table:** transcribe MAME's COL.0–15 (bit→ASCII) into a 16×N table.
2. **Keystroke queue:** a string/queue of chars to "type"; map each char → (column, row).
3. **74148 model:** for the BIOS-selected column, encode the pressed row → 3-bit code + GS.
4. **Port wiring:** Port C read returns {GS strobe, row code} for the selected column (the
   bit ekta37 polls); Port A/B return the column-select / key data per the 8255 config.
   (Confirm exactly which Port bits are column-select vs encoder-read from the 8255 control
   word + a short trace of the scan loop.)
5. **Feed + test:** queue e.g. a command, run ekta37, confirm it echoes/acts (VRAM changes).

This is a self-contained, well-defined build (MAME has the complete matrix + encoder); the
only RE step is confirming the exact Port-bit roles in the scan loop. Opt-in (like the
frame interrupt) so the byte-identical boot guard is untouched.
