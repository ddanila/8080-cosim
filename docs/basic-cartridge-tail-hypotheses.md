# BASIC cartridge tail hypotheses

Status: **SIMPLE TAIL HYPOTHESES REJECTED**

This generated report tests the easiest automatic reconstructions for
the missing Monitor 3.3 cartridge BASIC runtime page. It does not export
a replacement cartridge image; it records which simple media-shape
hypotheses are insufficient before any manual firmware reconstruction.

## Command

```sh
python3 scripts/report_basic_cartridge_tail_hypotheses.py
```

## Derived Constraint

For the relocation loop at runtime `0x2009..0x2013` to survive its
self-overwrite, the missing page at runtime `0x2100..0x21FF` must at
least reproduce the loop-tail bytes at offsets `0x09..0x13`:

```text
7e 12 23 13 0b 78 b1 c2 09 20 c3
```

A repository-wide binary scan over `roms/`, `ref/`, and `media/` finds
`1` page-shaped hit(s) for that exact page-offset
pattern:

| File | Page start | Pattern offset in page |
| --- | ---: | ---: |
| `roms/jbasic11.bin` | `0x01F00` | `0x09` |

The current scan finds no donor beyond the public cartridge's own final
page, which makes final-page mirroring the strongest simple hypothesis
to test first.

## Runtime Experiments

| Hypothesis | Change | Bytes | Probe run | Base-probe infra | Probe status | Cart reads | PC in 0x4000..0xBFFF | Mode-2 PC cycles | 0x00 opcode cycles | Nonzero BASIC-window bytes | Visible pixels | Stop PC |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| append-final-page | append a copy of the public cartridge final page; leave header bytes unchanged | 8448 | DONE | FAIL | BASIC RAM EXECUTION REACHED | 8196 | 17881962 | 0 | 17881962 | 0 | 0 | 0x9B6A |
| append-final-page-header-2100 | append the final page and patch header word `0x4005` to `0x2100` | 8448 | DONE | FAIL | BASIC RAM EXECUTION REACHED | 8452 | 17881963 | 0 | 17881963 | 0 | 0 | 0x9B6B |
| append-ff-header-2100 | append `0xFF` bytes and patch header word `0x4005` to `0x2100` | 8448 | DONE | FAIL | BASIC LAUNCH NOT YET REACHED | 8452 | 0 | 0 | 0 | 0 | 0 | 0xFF54 |
| append-zero-header-2100 | append zero bytes and patch header word `0x4005` to `0x2100` | 8448 | DONE | FAIL | BASIC RAM EXECUTION REACHED | 8452 | 17881963 | 0 | 17881963 | 0 | 0 | 0x9B6B |

## Interpretation

- Appending an extra page by itself does not alter the failing Monitor 3.3
  path, because the monitor still follows the cartridge's copy metadata.
- `Base-probe infra` is the inherited `basic_launch_probe.py` infrastructure
  check; it remains `FAIL` for these larger temporary variants because that
  base report expects the public 8192-byte cartridge size. `Probe run=DONE`
  means the bounded runtime experiment still completed and produced a row.
- Patching the visible header length to `0x2100` changes the monitor handoff
  registers, but the runtime cartridge bootstrap still carries its own
  `LXI B,0x2000` relocation length and still falls through into zero-filled
  `0x4000` RAM instead of rendering a BASIC prompt.
- Therefore the missing page is not recoverable by a fill byte, raw append,
  or final-page mirror alone. A defensible reconstruction needs either the
  real larger cartridge/programming artifact or a deeper patch-level
  understanding of the runtime bootstrap and expected low-memory image.

## Probe Excerpts

### append-final-page

- Handoff sample: `start: 0100->0107 src=ram op=C3 mode=1/1 bc=6000 de=2100 hl=0100 | 0107->2000 src=ram op=C3 mode=1/1 bc=6000 de=2100 hl=0100 | 2000->2003 src=ram op=21 mode=1/1 bc=6000 de=2100 hl=0100 | 2003->2006 src=ram op=11 mode=1/1 bc=6000 de=2100 hl=0200 | 2006->2009 src=ram op=01 mode=1/1 bc=6000 de=0100 hl=0200 | 2009->200A src=ram op=7E mode=1/1 bc=2000 de=0100 hl=0200 | 200A->200B src=ram op=12 mode=1/1 bc=2000 de=0100 hl=0200 | 200B->200C src=ram op=23 mode=1/1 bc=2000 de=0100 hl=0200 | 200C->200D src=ram op=13 mode=1/1 bc=2000 de=0100 hl=0201 | 200D->200E src=ram op=0B mode=1/1 bc=2000 de=0101 hl=0201 | 200E->200F src=ram op=78 mode=1/1 bc=1FFF de=0101 hl=0201 | 200F->2010 src=ram op=B1 mode=1/1 bc=1FFF de=0101 hl=0201; first `0x4000` entry: 3FFF->4000 src=ram op=00 mode=1/1 sp=FFD2 a=0E bc=F0FF de=0000 hl=8AD0`
- Mismatch sample: `0x0100..0x01FF` has `14` mismatches; `0x0200..0x1FFF` has `14` mismatches. Low mismatch samples: `a=0101 ram=FE cart=00 a=0102 ram=FF cart=D7 a=0111 ram=FE cart=FF a=0112 ram=FF cart=B3 a=0121 ram=FE cart=FF a=0122 ram=FF cart=B3 a=0129 ram=00 cart=99 a=012A ram=22 cart=1C a=0133 ram=CC cart=CD a=0134 ram=FF cart=B3 a=013F ram=00 cart=1F a=0140 ram=00 cart=02 a=0141 ram=56 cart=84 a=0142 ram=6F cart=87`

### append-final-page-header-2100

- Handoff sample: `start: 0100->0107 src=ram op=C3 mode=1/1 bc=6100 de=2200 hl=0100 | 0107->2000 src=ram op=C3 mode=1/1 bc=6100 de=2200 hl=0100 | 2000->2003 src=ram op=21 mode=1/1 bc=6100 de=2200 hl=0100 | 2003->2006 src=ram op=11 mode=1/1 bc=6100 de=2200 hl=0200 | 2006->2009 src=ram op=01 mode=1/1 bc=6100 de=0100 hl=0200 | 2009->200A src=ram op=7E mode=1/1 bc=2000 de=0100 hl=0200 | 200A->200B src=ram op=12 mode=1/1 bc=2000 de=0100 hl=0200 | 200B->200C src=ram op=23 mode=1/1 bc=2000 de=0100 hl=0200 | 200C->200D src=ram op=13 mode=1/1 bc=2000 de=0100 hl=0201 | 200D->200E src=ram op=0B mode=1/1 bc=2000 de=0101 hl=0201 | 200E->200F src=ram op=78 mode=1/1 bc=1FFF de=0101 hl=0201 | 200F->2010 src=ram op=B1 mode=1/1 bc=1FFF de=0101 hl=0201; first `0x4000` entry: 3FFF->4000 src=ram op=00 mode=1/1 sp=FFD2 a=0E bc=F0FF de=0000 hl=8AD0`
- Mismatch sample: `0x0100..0x01FF` has `14` mismatches; `0x0200..0x1FFF` has `7` mismatches. Low mismatch samples: `a=0101 ram=FE cart=00 a=0102 ram=FF cart=D7 a=0111 ram=FE cart=FF a=0112 ram=FF cart=B3 a=0121 ram=FE cart=FF a=0122 ram=FF cart=B3 a=0129 ram=00 cart=99 a=012A ram=22 cart=1C a=0133 ram=CC cart=CD a=0134 ram=FF cart=B3 a=013F ram=00 cart=1F a=0140 ram=00 cart=02 a=0141 ram=56 cart=84 a=0142 ram=6F cart=87`

### append-ff-header-2100

- Handoff sample: `-`
- Mismatch sample: `-`

### append-zero-header-2100

- Handoff sample: `start: 0100->0107 src=ram op=C3 mode=1/1 bc=6100 de=2200 hl=0100 | 0107->2000 src=ram op=C3 mode=1/1 bc=6100 de=2200 hl=0100 | 2000->2003 src=ram op=21 mode=1/1 bc=6100 de=2200 hl=0100 | 2003->2006 src=ram op=11 mode=1/1 bc=6100 de=2200 hl=0200 | 2006->2009 src=ram op=01 mode=1/1 bc=6100 de=0100 hl=0200 | 2009->200A src=ram op=7E mode=1/1 bc=2000 de=0100 hl=0200 | 200A->200B src=ram op=12 mode=1/1 bc=2000 de=0100 hl=0200 | 200B->200C src=ram op=23 mode=1/1 bc=2000 de=0100 hl=0200 | 200C->200D src=ram op=13 mode=1/1 bc=2000 de=0100 hl=0201 | 200D->200E src=ram op=0B mode=1/1 bc=2000 de=0101 hl=0201 | 200E->200F src=ram op=78 mode=1/1 bc=1FFF de=0101 hl=0201 | 200F->2010 src=ram op=B1 mode=1/1 bc=1FFF de=0101 hl=0201; first `0x4000` entry: 3FFF->4000 src=ram op=00 mode=1/1 sp=FFD2 a=0E bc=F0FF de=0000 hl=8AD0`
- Mismatch sample: `0x0100..0x01FF` has `14` mismatches; `0x0200..0x1FFF` has `7` mismatches. Low mismatch samples: `a=0101 ram=FE cart=00 a=0102 ram=FF cart=D7 a=0111 ram=FE cart=FF a=0112 ram=FF cart=B3 a=0121 ram=FE cart=FF a=0122 ram=FF cart=B3 a=0129 ram=00 cart=99 a=012A ram=22 cart=1C a=0133 ram=CC cart=CD a=0134 ram=FF cart=B3 a=013F ram=00 cart=1F a=0140 ram=00 cart=02 a=0141 ram=56 cart=84 a=0142 ram=6F cart=87`
