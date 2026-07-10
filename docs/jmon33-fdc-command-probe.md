# jmon33 FDC T-command probe

Status: **JMON33 FDC T-COMMAND ORACLE PINNED**

This cosim diagnostic pins Monitor 3.3's `T` command behavior after the
monitor-idle cursor, both with no disk-backed FDC and with the vendored
`media/disks/JUKU1.CPM` image. It provides a command-level oracle for the
current structural HDL FDC probe; keyboard sampling works, while the resumed
`T` path enters heavy FDC I/O.

## Command

```sh
sync/jmon33_fdc_command_probe.py
```

Environment overrides:

- `JMON33_FDC_COMMAND_MAX_CYCLES` default `60000000`
- `JMON33_FDC_COMMAND_FRAME_CYCLES` default `200000`
- `JMON33_FDC_COMMAND_START_VRAM` default `210`
- `JMON33_FDC_COMMAND_HOLD_FRAMES` default `20`
- `JMON33_FDC_COMMAND_GAP_FRAMES` default `6`
- `JMON33_FDC_COMMAND_DISK` default `media/disks/JUKU1.CPM`

## Evidence

| Scenario | Disk | Exit | Stop PC | Cycles | FDC events | FDC data reads | FDC status reads | FDC command writes | First commands | Cursor | Visible blocks | Pixels | VRAM SHA256 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | --- |
| no-disk | `none` | `0` | `0xFF54` | `60000002` | `185` | `0` | `103` | `22` | `0xFD`, `0xFD`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5`, `0xE5` | `yes` | `x=8,y=20`, `x=296,y=60` | `160` | `9da43c195487eae0eeac8c65725a3251ff502642025b745a16691a1d7044bae3` |
| JUKU1.CPM | `media/disks/JUKU1.CPM` | `0` | `0xFF54` | `60000008` | `1788113` | `0` | `1788112` | `1` | `0xFD` | `yes` | `x=8,y=20`, `x=152,y=40` | `160` | `124da9303e7496bf2b45a20935107aed5207e2739ab06c6aa2f7376afaf07b99` |

## FDC Trace Anchors

### no-disk

- First FDC line: `[IOSEQ] OUT port=0x1C value=0xFD cyc=9237266 pc=E2B7 g_vw=230 count=1`
- Last FDC line: `[IOSEQ] IN  port=0x1C value=0xE5 cyc=10818402 pc=E43C g_vw=230 count=103`

### JUKU1.CPM

- First FDC line: `[IOSEQ] OUT port=0x1C value=0xFD cyc=9237266 pc=E2B7 g_vw=230 count=1`
- Last FDC line: `[IOSEQ] IN  port=0x1C value=0x40 cyc=60000008 pc=E43C g_vw=420 count=1788112`

## Disposition

- The no-disk row is the closest cosim comparison for a monitor command
  oracle generated without `JUKU_DISK`.
- The `JUKU1.CPM` row is the disk-backed oracle to compare against HDL
  runs where the structural FDC is visible and serviced.
- With the read-only raw-image backend, command `0xFD` is treated as a
  Type-III write-track command and completes with status `0x40` WRITE
  PROTECT rather than staying BUSY forever. Monitor 3.3 keeps polling
  that status in this bounded run, so the disk-backed row is a stable
  write-protect oracle, not a successful disk operation.
- This is still a command-level oracle, not a full EKDOS boot proof;
  full ROMBIOS `TDD` boot remains tracked by the EKDOS/FDC probes.
