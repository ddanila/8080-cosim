# EKDOS source references

Vendored public Juku/EKDOS source references from Arti's Juku software mirror.
These are preservation artifacts and behavioral references for the ROMBIOS,
EKDOS, and WD1793/VG93 boot path work; they are not small-PROM programming
payloads.

## Provenance

| File | Source URL | Size | SHA256 | Role |
| --- | --- | ---: | --- | --- |
| `EKDOS30.ASM` | `https://arti.ee/juku/tarkvara/EKDOS30.ASM` | 14336 | `9d0d06147597b4039bbbfdb31b98adc17168da2e354962ec12423b385e0ced3d` | 52K EKDOS 2.30 CP/M BIOS source for Juku; records monitor entry points, disk geometry, and floppy handler interface. |
| `axb.asm` | `https://arti.ee/juku/tarkvara/axb.asm` | 8652 | `a776f6adebd38503eb2566e0160ea35f1805f1e4d315022cb73bc7502e6db0b7` | Generic CP/M BIOS skeleton/reference from the same software mirror. |

## Checks

```sh
(cd ref/ekdos-source && sha256sum -c SHA256SUMS)
```

`sync/reference_artifact_check.sh` includes this directory in CI.

## Source limitations

`EKDOS30.ASM` contains interleaved and malformed lines, including
`SEKTRK equ fbi+1MDISKPAR` and a split BIOS jump-vector instruction.
Preserve those original bytes; this copy is a reference for selected constants
and routines, not a verified buildable BIOS source. The
[inspection report](../../docs/ekdos-source-inspection.md) checks selected
symbols and line presence without assembling or executing the source.

## Notes

- `EKDOS30.ASM` describes a 52K EKDOS 2.30 BIOS compatible with Bootstrap
  4.x and a DEC Rainbow-derived 80-track, double-sided disk format. Its monitor
  calls include `FLOPPY`, `START`, and `RWFLOPPY`, matching the ROMBIOS/FDC
  interface exercised by the current `TDD` probes.
- D2/D6/D8/D94 programming evidence is maintained separately in
  [the physical PROM reference](../physical-proms/README.md), with links to
  the decode and circuit constraints.
