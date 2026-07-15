# Monitor 2.2 reconstruction audit

Status: **ONE BYTE PROVEN / ROM BLOCKS 6-7 UNRESOLVED**

This generated audit identifies the only Monitor 2.2 byte that current
repository evidence can reconstruct without guesswork. It preserves
`roms/jmon22.bin` unchanged and exports only a machine-readable patch
manifest; no partially repaired ROM binary is published.

## Command

```sh
python3 scripts/report_jmon22_reconstruction.py
```

## Source guard

| Artifact | Size | SHA256 |
| --- | ---: | --- |
| `roms/jmon22.bin` | `16384` | `1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589` |
| `roms/jmon33.bin` | `16384` | `ce9e9c63abbb1780566423a871081bd0bf048a2f3c79e370b465ea9869ff51b8` |
| `roms/jbasic11.bin` | `8192` | `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60` |
| `roms/ekta24.bin` | `16384` | `e1bd9894134ee4085c14bde854780539d3b1e03cfc032c81ec352729e9d69287` |
| `roms/ekta31.bin` | `16384` | `26f1f4161a547ea60312a250bde9df41c0b07a939c0b880628050eaec18ec4e4` |
| `roms/ekta32.bin` | `16384` | `1826563e23b5d8bc23c61694ceccb923d6a31778077934ad0338772070671122` |
| `roms/ekta35.bin` | `16384` | `e8fe5e657037b8f3203f57512cd01cc35f7eaa2a3f0dae8d0ae19378908bd518` |
| `roms/ekta37.bin` | `16384` | `fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27` |
| `roms/ekta43.bin` | `16384` | `39e3ca8978b369632d03c658300654445b898139009f188cb154e2f901238ba7` |

## Proven correction

| Candidate | Monitor 2.2 | Monitor 3.3 | BASIC 1.1 cartridge | Checksum effect |
| --- | --- | --- | --- | --- |
| Monitor offset `0x1EFC` | `0x9A` | `0xDA` at `0x1EFC` | `0xDA` at mapped offset `0x1C34` | block 3 `0xF3` -> stored `0x33` |

Monitor 3.3 and the separately packaged cartridge agree on `0xDA` across
their otherwise byte-identical 7,224-byte BASIC body. Substituting that
value for Monitor 2.2's sole body mismatch adds `0x40`, exactly closing
the stored additive checksum. These three constraints converge on one
correction; the manifest records it without rewriting the source image.

## Checksum boundary

| Block | Covered bytes | Stored | Before | After | Disposition |
| ---: | --- | ---: | ---: | ---: | --- |
| `0` | `0x0004..0x07FF` | `0xD2` | `0xD2` | `0xD2` | PASS |
| `1` | `0x0800..0x0FFF` | `0x72` | `0x72` | `0x72` | PASS |
| `2` | `0x1000..0x17FF` | `0x0A` | `0x0A` | `0x0A` | PASS |
| `3` | `0x1800..0x1FFF` | `0x33` | `0xF3` | `0x33` | REPAIRED BY PROVEN BYTE |
| `4` | `0x2000..0x27FF` | `0x6E` | `0x6E` | `0x6E` | PASS |
| `5` | `0x2800..0x2FFF` | `0x31` | `0x31` | `0x31` | PASS |
| `6` | `0x3000..0x37FF` | `0x91` | `0x51` | `0x51` | UNRESOLVED (checksum delta `+0x40`) |
| `7` | `0x3800..0x3FFF` | `0x58` | `0xB5` | `0xB5` | UNRESOLVED (checksum delta `+0xA3`) |

The public JUKUROMS catalog says the seventh physical chip was read with
a couple of errors and the eighth produced 50 divergences over seven read
attempts ([source](https://j3k.infoaed.ee/tarkvara-kataloog/), checked 2026-07-15). Those are
zero-based blocks 6 and 7 in this concatenated image—the same two blocks
that remain bad after the proven correction.

A checksum delta constrains only the sum of a 2 KiB block. It neither
locates damaged bytes nor determines their values, particularly when the
preservation source explicitly reports multiple unstable reads. Blocks 6
and 7 therefore remain untouched until original per-read captures, a stable
independent dump, or another byte-identical firmware source is recovered.

## Related-ROM donor search

The audit tests every one-byte checksum repair with three source bytes
available on each side against all seven other tracked 16 KiB monitor/BIOS
images. This covers all 2,048 block-6 positions and 2,045 block-7
positions; only the ROM's final three bytes lack right-hand context. A donor
must contain the proposed replacement byte with the same three bytes on each
side, so a moved routine can match without assuming a fixed ROM address.

| Block | Required delta | One-byte checksum solutions | Context-tested | One-bit subset | 2-byte-flank matches | 3-byte-flank donors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `6` | `+0x40` | `2048` | `2048` | `898` | `0` | `0` |
| `7` | `+0xA3` | `2048` | `2045` | `0` | `6` | `0` |

Block 7's six short-context matches are one false donor repeated across all
six EktaSoft images: changing `0x3BAA` from `0x21` to `0xC4` would close
the checksum, but it would turn Monitor 2.2's first vector initializer from
`LXI H,$FF21; SHLD $0031` into `$FFC4`. The EktaSoft match is its distinct
second initializer, `LXI H,$FFC4; SHLD $0001`; extending the context from
two to three bytes on each side correctly rejects the semantic misalignment.

The zero three-byte-context result matters in both directions: no tracked
related ROM supplies a checksum-closing byte in matching local code, while the
checksum alone leaves 2,048 possible one-byte edits per block. Block 6 still
has 898 checksum-closing edits that are literal one-bit changes. Choosing
among them from opcode plausibility or later-version address relocation would
be guesswork, and block 7 cannot be repaired by any single-bit edit at all.
The original multi-read captures or a second Monitor 2.2 dump remain required.

## Preservation rule

- Original SHA256: `1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589`.
- Hypothetical one-byte-patched SHA256: `37c3d2db23dbccb8b7a81a2510f320d50e30f04a260fa6c8efd132241a4675a5`.
- Patch manifest: `ref/reconstructed-firmware/jmon22-consensus-patch.json`.
- Do not treat the hypothetical hash as a runnable or complete Monitor 2.2
  release: its final two ROM blocks still fail their own checksums.
