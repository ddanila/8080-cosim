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

## Preservation rule

- Original SHA256: `1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589`.
- Hypothetical one-byte-patched SHA256: `37c3d2db23dbccb8b7a81a2510f320d50e30f04a260fa6c8efd132241a4675a5`.
- Patch manifest: `ref/reconstructed-firmware/jmon22-consensus-patch.json`.
- Do not treat the hypothetical hash as a runnable or complete Monitor 2.2
  release: its final two ROM blocks still fail their own checksums.
