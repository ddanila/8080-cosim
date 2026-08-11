# Annotated ROM disassemblies

SkoolKit-based, round-trip-guarded disassemblies of the vendored Juku ROMs.
The maintained artifact is the **control file** (`.ctl`): labels, comments,
and code/data boundaries accumulate there. The `.skool` file is generated
from it and vendored for browsing; it must always regenerate identically and
reassemble to the exact pinned ROM bytes.

## ekta37 (EktaSoft '88 Serial #0037, RomBios 3.43m)

- [`ekta37/ekta37.ctl`](ekta37/ekta37.ctl) — hand-maintained knowledge.
- [`ekta37/ekta37.skool`](ekta37/ekta37.skool) — generated disassembly.

Memory model (byte-verified, see the ctl header): ROM `0000-17FF` executes in
place; ROM `1800-3FFF` is relocated to RAM at `+C000h` and executes at
`D800h-FFFFh` — the EKDOS monitor vectors at runtime `FF50h` are ROM
`3F50h`. Addresses in the ctl/skool are ROM file offsets.

The initial code map was seeded by recursive descent from the reset entry
and the monitor vector table, translating control-flow targets in
`D800h-FFFFh` back by `-C000h`, plus the byte-verified NetBios entries from
[`../docs/ekta37-netbios-notes.md`](../docs/ekta37-netbios-notes.md).
Regions not yet proven code remain `b` (data) blocks; refine them in the ctl
as understanding grows, never by editing the skool.

## Workflow

```sh
# Install once (any machine; also done automatically by the check script):
python3 -m venv ~/.venvs/skoolkit && ~/.venvs/skoolkit/bin/pip install skoolkit==10.0

# After editing the ctl, regenerate the vendored skool:
sna2skool.py --hex --org 0 --start 0 --end 16384 \
  --ctl disasm/ekta37/ekta37.ctl roms/ekta37.bin > disasm/ekta37/ekta37.skool

# Guard (also runs in generic CI):
sync/ekta37_disasm_check.sh
```

The guard asserts three identities: the pinned `roms/ekta37.bin` SHA256, the
vendored skool regenerating byte-identically from the ctl, and
`skool2bin.py` reassembling the skool to the exact ROM bytes.

## Caveats

- SkoolKit emits **Z80 mnemonics** for this 8080 machine. Round-trip is
  unaffected, but read carefully: byte `08h` displays as `EX AF,AF'`, which
  on the real КР580ВМ80А/8080 is an undocumented NOP; Z80-only semantics
  must never be inferred from the listing. Cross-check questionable
  instructions with `cosim/dis8080.py` (exact Intel mnemonics).
- SkoolKit is pinned to 10.0; a version bump must regenerate the skool and
  re-run the guard.
