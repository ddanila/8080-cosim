# Emu80v4 Juku/FDC survey

Status date: 2026-07-07.

Source inspected: `https://github.com/vpyk/emu80v4`, shallow clone at survey time.

## License Boundary

Emu80v4 is GPL-3.0-or-later. Do not copy its C++ implementation into this
repository unless we deliberately accept a GPL-3-compatible boundary. For now it
is an external behavioral reference only.

## Juku Coverage

No Juku-specific machine driver, config, ROM set, or media set was found in the
repository during this survey:

```sh
find /tmp/emu80v4 -iname '*juku*' -o -iname '*510*' -o -iname '*ekdos*'
```

The project therefore does not add new Juku ROM, keyboard, video, schematic, or
EKDOS media evidence beyond the public sources already tracked here.

## Useful FDC1793/VG93 Reference Points

Emu80v4 does include a generic `Fdc1793` / КР580ВГ93 implementation used by
several other Soviet-machine targets. Compared with our bounded HDL shim, it
models additional controller behavior worth using as a checklist if our
`juku_top` EKDOS work later proves blocked on FDC fidelity:

- Type-I command family beyond restore/seek: step, step-in, and step-out update
  the track register and direction state.
- Type-II sector access includes read and write paths plus multi-sector command
  timeout handling.
- Type-III read-address returns an ID tuple derived from current track, head,
  sector, and sector-size code.
- Write-track accepts ID and data address marks and uses the decoded ID field to
  select the sector before writing data bytes.
- Status handling includes not-ready/image-present checks, track-zero status,
  index pulse status during Type-I/force-interrupt style polling, write-protect
  status, and record-not-found style failures.
- DRQ is represented as active while a transfer is in progress; IRQ is asserted
  when a command or transfer completes.
- Its disk-image addressing is the same linear raw-sector shape we already use:
  `(sector + (head + track * heads) * sectors_per_track) * sector_size`.

## Adoption Decision

No code or binary artifact is adopted from Emu80v4. The useful adoption is the
reference checklist above, plus the decision to keep Emu80v4 in
`docs/fdc-core-survey.md` as a mature GPL-3 software-model reference.

For the current plan, this does **not** change the immediate M2 target. Our
top-level HDL probe still has to reach ROMBIOS PIC/PPI/FDC activity and then the
EKDOS `A>` prompt with vendored `media/disks/JUKU1.CPM`. If controller fidelity
becomes the blocker after decoded FDC I/O is reached, revisit this survey before
expanding the local shim.
