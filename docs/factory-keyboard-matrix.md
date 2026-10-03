# Factory keyboard matrix — `ДГШ5.104.015 Э3`

Generated from the retained transcription in `scripts/report_keyboard_matrix.py`.
The generator verifies the three source-photo hashes and compares cosim source
mapping tuples with its expected tuples. It does not reread the photographs,
simulate the HDL, or verify physical keyboard continuity. The transcription is
an electrical coordinate map; host-key placement and physical fit need separate
checks.

Regenerate with `python3 scripts/report_keyboard_matrix.py`.
`sync/keyboard_matrix_check.sh` also requires the generated report to match the
tracked copy.

## Coordinate result

The drawing numbers its fifteen decoder outputs 1–15; software therefore writes
factory line minus one to PPI D26 Port A bits PA0–PA3 (`SC0–SC3`).  The six
horizontal buses are deliberately not binary ordered: factory rows 1–6 reach
the model's 74148 input bits 4, 3, 5, 1, 0, and 2 respectively.  D1/D2 encode
those inputs onto `K0–K2`; their diode OR produces active-low `-FK`.  `SHIFT`
and `CTRL` bypass the matrix encoder and appear separately on X1.

| factory line | model column | row 5 / bit 0 | row 4 / bit 1 | row 6 / bit 2 | row 2 / bit 3 | row 1 / bit 4 | row 3 / bit 5 |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 1 | 0 | F6 | N | — | Y | 6 / & | H |
| 2 | 1 | — | X | — | W | 2 / " | S |
| 3 | 2 | F4 | V | — | R | 4 / $ | F |
| 4 | 3 | F1 | — | — | TAB | ESC | CAPS LOCK |
| 5 | 4 | F5 | B | — | T | 5 / % | G |
| 6 | 5 | F2 | Z | — | Q | 1 / ! | A |
| 7 | 6 | F3 | C | — | E | 3 / # | D |
| 8 | 7 | F7 | M | — | U | 7 / ' | J |
| 9 | 8 | — | — | DEL | ] / õ | ERASE | RETURN |
| 10 | 9 | — | — | ↓ | [ / ö | Ä / Ü | — |
| 11 | 10 | — | — | ↑ | õ / Õ | Ö / Õ | : / * |
| 12 | 11 | — | ; / + | SPACE | \ / ^ | - / = | ä / Ä |
| 13 | 12 | — | / / ? | → | P | 0 / _ | ö / Ö |
| 14 | 13 | — | . / > | ← / BACKSPACE | O | 9 / ) | L |
| 15 | 14 | F8 | , / < | LAT/RUS | I | 8 / ( | K |

Shifted punctuation is shown after `/`.  Paired national legends separated by
`/` are literal cap legends and remain a firmware/font interpretation boundary.

## Connector X1

| pin | net | role |
| ---: | --- | --- |
| 1 | `K2` | encoded matrix row |
| 2 | `K0` | encoded matrix row |
| 3 | `K1` | encoded matrix row |
| 4 | `-FK` | active-low key-present flag |
| 5 | ground | supply return |
| 6 | `+5V` | supply |
| 7 | `SHIFT` | dedicated modifier return |
| 8 | `CTRL` | dedicated modifier return |
| 9 | `CONTRDAT` | serialized S21 configuration-switch return |
| 10 | — | no connection shown |
| 11 | `SC0` | scan-address bit |
| 12 | `SC1` | scan-address bit |
| 13 | `SC2` | scan-address bit |
| 14 | `SC3` | scan-address bit |

## Configuration switches S21

The keyboard drawing contains an eight-position `S21` bank labelled
`НАСТРОЙКА` (configuration).  During scan positions 8–15 its selected switch
returns serially on `CONTRDAT` to the mainboard E8.4 selector terminal. The
exact `.009` sheet-1 drawing sends D26 PB4/pin22 to E8.3 and PB5/pin23 to
E8.2; the `.009` assembly and owner photo show the 3–4 bridge fitted. The
replica netlist now assigns this return to PB4; its routed copper remains open
pending A50 hole identification and direct continuity.

EktaSoft 3.7 decodes the S21 bits as follows, but its archived ROM bytes at
`1211h..1216h` (`DB 05 2F FB E6 20`) mask **PB5**, not PB4. That ROM profile
and the photographed `.009` 3–4 bridge therefore disagree on the selected
input; see `docs/ekta37-netbios-notes.md`.

| switch | configuration bit | NetBios meaning |
| ---: | ---: | --- |
| S21.1 | 7 | interface: onboard D11 or expansion interface |
| S21.2–S21.3 | 6–5 | maximum station number: 3, 7, 15, or 31 |
| S21.4–S21.8 | 4–0 | this station's number |

In the EktaSoft 3.7 PB5 simulation profile, a nonzero configuration accepts
`TN` with no Enter and takes network identity from S21. A zero configuration
falls through to the ROM's `N=` and `S=` keyboard prompts; cosim deliberately
models that open-switch fallback and therefore injects `TN0201`. The same
behavior on the `.009` PB4-strapped board remains unverified.

The implemented network-first ROM uses reset-latched S21 configuration shared
with CP/M. Bits 2:1 select 40x24, 53x24, 64x20 or 80x24; bits 4:3 select
English, Estonian, CP866 Russian or English/user-remap. C4--C8 use bit 0 for
automatic boot versus local recovery wait; C9 and successors reserve it and
always boot from the network. This software policy does not resolve the
archived EktaSoft PB5 versus photographed PB4 selector boundary above.
See [the network-ROM contract](../spinoffs/jukuravi/network-rom/README.md)
and [C12 qualification](c12-runtime-console.md) for runtime overrides and
physical acceptance scope.

## Model comparison

- All 26 letters, ten digits, their drawing-visible ASCII shift pairs, Space,
  Return, Tab, Escape, Backspace/Left, and ASCII punctuation now have exact
  drawing-derived cosim tuples.  Uppercase letters assert the dedicated SHIFT
  return while reusing the lowercase matrix contact.
- The HDL accepts the same `(column, key-bit, shift)` tuple at its simulation
  boundary; shifted `T` remains column 4, bit 3 and reads as Port B `0x88`.
- No-key remains `0xCF`: `K0–K2` and `-FK` released, SHIFT/CTRL released.
- Interactive PTY bytes `80`..`91` (except `85` and `8e`) inject the guarded
  Down, Erase, F5, F6, F8, Shift-F8, F1, F2, F3, F4, Up, Right, Left,
  Shift-Up, Shift-Down, and F7 contacts. `85` and `8e` inject Ctrl-Up/Home and
  Ctrl-Down/End outside `KMAP`. These bytes are a cosim test protocol, not
  character encodings exposed to Juku software.
- `JUKU_KEY_AT_PC=PC:BYTE` begins one of those same mapped contacts at an exact
  guest instruction boundary and then applies the ordinary hold/release frame
  timing. `JUKU_KEY_AT_PC_HOLD_FRAMES` can lengthen only that one triggered
  contact across a slow guest operation without changing queued-key timing;
  `JUKU_KEY_AT_PC_GATE=ADDRESS:BYTE` can additionally require a guest-memory
  byte before the one-shot trigger is armed. It is the deterministic raw-poll
  test interface; it does not return a key value directly or bypass the
  matrix.
- The C7 ABI fixture feeds raw bytes `86` and `85` directly through this
  matrix model and requires the public raw-key vector to return column/PB
  pairs `0E/8E` and `0A/6A`. This is an executable regression for the exact
  modified contacts, not an inference from translated ASCII input.
- The matrix transcription includes contacts beyond the ASCII and synthetic
  tuple sets listed above. Those stimulus checks do not establish complete
  host-byte coverage of every locking, national or mode-switch contact.
