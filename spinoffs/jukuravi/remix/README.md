# ekta4401 — the EktaSoft #0037 remix ROM

Phase 1 complete, 2026-08-11. A derived 16 KiB image built deterministically
from the pinned `roms/ekta37.bin`. Plan and phase results:
[`../EKTA37-REMIX-PLAN.md`](../EKTA37-REMIX-PLAN.md).

- Image: [`ekta4401.bin`](ekta4401.bin), SHA256
  `df067d1c452866ad590e548a1d753375b77c39e83e4cd91599c18aba44e3cbfa`
- Builder: [`build_ekta4401.py`](build_ekta4401.py) (`--check` verifies the
  committed image rebuilds identically)
- Guard: `sync/ekta4401_check.sh`, test
  [`../../../tests/ekta4401_remix_test.py`](../../../tests/ekta4401_remix_test.py)

**This is not a factory image.** Its banner says so: the stock identity line
`'EktaSoft '88  Serial #0037` is replaced, same length, by
`'EktaSoft&D.Sukharev '26#01` — the co-author is named in the banner and the
year is '26. The file name encodes serial **44** (one past #0043, the highest
known factory serial) and build **01**; 44 is this project's convention, not
a factory-assigned number. No byte of the archival #0037 pair is affected;
that image remains the replica content truth.

## Phase 1 content

| Change | ROM bytes |
| --- | --- |
| Banner identity line | `00DF-00F9` (in place, same length) |
| Command dispatch table relocated + `H` added | `3900-3937` (runtime `F900h`) |
| `H` handler (`LXI B,text` / `CALL DA6Bh` / `RET`) | `3931-3937` |
| Help text | `3938-39CB` |
| Table pointer repointed (`LXI H,F900h`) | `1924-1925` |
| Eight chunk checksums regenerated | `0008-000A`, `1806-180A` |

Everything else is byte-identical to ekta37. Total footprint of the new
code and data: 203 bytes in the `3900h` free gap, leaving 1,263 bytes of it
for the Phase 2 Jukuravi module.

## Checksum convention (recovered here)

The boot verifier checks **eight 2 KiB chunks in two regions**, with stored
bytes *descending* from a header byte — not the single block-1 sum of the
Jukuravi-era convention:

| Region | Chunks | Stored bytes |
| --- | --- | --- |
| low | `000B-07FF`, `0800-0FFF`, `1000-17FF` | `000A`, `0009`, `0008` |
| upper | `180B-1FFF`, `2000-27FF`, `2800-2FFF`, `3000-37FF`, `3800-3FFF` | `180A`, `1809`, `1808`, `1807`, `1806` |

All eight sums verify against stock ekta37, and the builder regenerates all
eight. A patched image that updates only the block-1 byte fails the ROM's
own verifier and never reaches the command prompt — observed during Phase 1.

## Validation

Static: rebuild identity, a bounded patch set (any byte changed outside the
listed ranges fails), all eight chunk checksums, the banner identity, and
**every stock command still dispatching to its original handler**.

Behavioral (cosim): the image boots and paints a banner screen; with `H`
typed, the CPU bus trace shows the relocated table scanned (196 reads), the
new handler executed (28), and the help text walked (592). Bus-trace
evidence is used deliberately instead of pixel decoding — the console
renders inverted, proportional-ish glyphs whose exact cell mapping is not
yet reverse-engineered, so pixel assertions would be fragile.

## Not yet done

Phase 2: port the Jukuravi loader core into the remaining gap, add the `J`
command, and strip the floppy subsystem for the space it needs. No physical
burn has happened; the image is desk-validated only.
