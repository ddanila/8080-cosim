# C12 runtime console contract and physical qualification

Status: **CORRECTED CP437, WARM/DEFAULT, RESET AND POWER-CYCLE CHECKS
PASSED ON CS00000; BROADER RELEASE QUALIFICATION SEPARATE**

## Physical qualification

On CS00000, the original C12 pair passed cold STATUS/DIAG and owner-confirmed
40x24 English, 53x24 Estonian, and 64x20 Russian VIDTEST pages. Its 80x24
user/remap page failed visual acceptance: DAh/D9h corners appeared as `?`.
The failed run stopped before RESET/power-cycle checks; its retained evidence
is `out/physical-CS00000-c12-runtime-attended-20260905` in the sibling CP/M
project.

The resident CP437 lookup still searched 17 entries after its table expanded
to 26. Nine trailing entries, including D9h and DAh, therefore fell back to
`?`. C12 now derives its search count from the code-table extent. C4--C11
artifacts remain unchanged. The expanded C12 regression renders every byte
B0h..DFh through the public console ABI in all four runtime-selected character
banks at 80 columns, comparing the framebuffer with the independent oracle.
It reproduces the old failure and passes after the correction.

Only D16 changes, including its checksum balance; D15 remains byte-identical.
The original installed combined hash was
`724f672657390882f10c19588778527bd0b46848616ccf4ec348502dbb36e18b`,
with D16 `45193e069ee3dca7a0abf98a20a563959c2a760e9eca828659d69a76420fe9b4`.
Earlier physical and Wine evidence belongs to that original pair. The hashes
below identify the corrected candidate. Its focused physical glyph and
lifecycle checks subsequently passed, as recorded below.

### Corrected D16 physical recheck

D15 was retained and corrected D16 was programmed and verified in DOSRAVI
session `at28c64-jukunet-c12-cp437-d16-write-20260905`. The owner fitted D16
and confirmed the startup checkerboard.

These sessions under the sibling `cpm-plus-juku/out/` passed their workloads
and `physical_acceptance.py audit`:

| Session suffix (prefix `physical-CS00000-c12-`) | Evidence |
| --- | --- |
| `cp437-recheck-20260905` | owner confirmed corrected 80x24 user/remap corners and sample glyphs, then pressed physical Return; 7/7 commands passed, including warm-boot override preservation, default restoration and DIAG ALL |
| `reset-prepare-20260905` | 4/4 commands proved 40x24 / Russian with both overrides set before the owner pressed RESET |
| `after-reset-20260905` | checkerboard confirmed by owner; 2/2 commands proved 80x24 / Estonian, both overrides clear, clean cold state and DIAG ALL |
| `powercycle-prepare-20260905` | 4/4 commands re-established 40x24 / Russian with both overrides set |
| `after-powercycle-20260905` | owner confirmed off/on and checkerboard; 2/2 commands proved S21 0F defaults restored, both overrides clear, clean cold state and DIAG ALL |

All five host summaries report zero retries and UART errors. Cold runs retain
warnings for missed V16 ready/final markers; the existing recovery path reached
NetDisk without retransmission. RESET/power-cycle checks started a host after
the checkerboard appeared; they do not prove reset recovery with a continuously
running host. The 40/53/64-column visual confirmations belong to the original
pair; the corrected pair received the focused 80-column recheck. Original
failed session records remain unchanged. These results do not qualify Windows
hardware, a new endurance run, or all three unmodified release profiles.

Byte-exact original CS00000 transcripts are retained in the sibling CP/M
project under `tests/fixtures/c12-CS00000-20260905/` for offline replay and
negative tests.

C12 is an additive successor to the immutable C11 ROM. It switches video
geometry and character bank at runtime without changing S21 or resetting the
machine. Its passive boot beacon identifies C12 to the host.

## ABI 1.5 contract

Feature bit `1000h` and vector `FF5Fh` identify `JCGCONCONFIG`:

| A | Operation | Inputs | Successful result |
| ---: | --- | --- | --- |
| 0 | query | none | A=reset-latched S21, B=active mode, C=active bank, D=override flags |
| 1 | set | B=mode 0..3, C=bank 0..3 | applies the complete pair, A=0/CY clear |
| 2 | default | none | reapplies S21 bits 4:1, A=0/CY clear |

Modes 0..3 select 40x24, 53x24, 64x20 and 80x24 respectively. Banks 0..3
select English, Estonian, CP866 and English/user-remap respectively.

Other selectors or a mode/bank outside 0..3 return A=`FFh` with carry set and
change neither state nor pixels. Override flag bit 0 means video differs from
S21; bit 1 means the character bank differs. The flags are independent.

A successful transition hides the old cursor, selects the new timing and font
policy, clears the complete 9,648-byte physical-raster envelope, resets cursor
position/blink, discards a pre-switch pending key without erasing the
persistent four-pair key-remap table, and publishes the active pair before
returning. Calls are synchronous under the existing interrupt-disabled ROM
ABI. Ordinary console initialization and CP/M warm boot preserve the active
override. Reset or an explicit `JCGINIT` restores the latched S21 default and,
as before, resets the key-remap table.

The ABI 1.5 call-gate addition consumes exactly the five bytes that remained in
the fixed 224-byte `D620h` envelope. Active configuration and flags occupy
`D7FDh..D7FEh`, the only two-byte gap after the resident-host block; the
console state ending at `D7D9h`, per-drive NetDisk state at `D7DAh..D7DFh`,
host state at `D7E0h..D7FCh`, fixed `D600h..D7FFh` reservation, and CP/M TPA
remain unchanged.

## Boot discovery identity

The host remains receive-only during discovery. The C12 ROM periodically
transmits checked frame `4A 42 0C 01 05` (`JB`, C12, flags 1, checksum 05)
at 19,200/8O1, then listens for Fastboot at 19,200/8N1, following the
[C11 recovery wire contract](c11-session-recovery.md#wire-contract).
C11 retains its byte-identical `JB/11` frame. The production host accepts
both identities and logs the received ROM generation; random or malformed
data does not select a boot path.

## Qualification and immutable boundary

`tests/network_first_rom_c12_test.py` proves:

- deterministic ABI 1.5 metadata, manifest, feature bit, `FF5Fh` vector, and
  exact 224-byte low-RAM gate;
- the immutable C11 combined SHA-256 remains
  `b93428bb33cd7e31c2d9b2b84aa07ea17edda76c9d53ab73b3cb8687e8d53dfd`;
- rejected selectors, mode values, and bank values do not publish partial
  state;
- all 16 runtime mode/bank pairs render against the independent font oracle,
  clear the physical raster tail, retain distinct defaults and active state,
  preserve an installed `T`-to-`X` key remap, and survive ordinary console
  reinitialization.

The aggregate `sync/network_first_rom_abi_check.sh` retains every C4--C11
regression before running that C12 matrix. The deterministic simulator
artifacts are:

- combined: `b1a8152c0b4684d9d5608bd8bb60a06a21393c3bd7e7894cd8b7b61c494350d6`;
- D15 low: `b95eb5b0842d501ee602d82a7907b1cf4baf3e1b2cd74f73ef553eac60faf9de`;
- D16 high: `3c6530816ed114f8a6d612c2b023a67a841b4e0c323754a9692d0d197664dd8a`.

`sync/network_first_rom_hdl_check.sh` also runs the C12 ABI self-test through
the structural VM80A/Juku model, including call-gate dispatch, POF release,
runtime transition, retained remap, translated keyboard input, and serial
completion. The exhaustive 4x4 framebuffer oracle remains in the faster
C-model matrix.

## Companion implementation and remaining qualification

The sibling CP/M project implements `CONSOLE` query/set/default, active-state
STATUS/DIAG reporting, and C12-specific `VIDTEST`. Its named system, Fastboot,
release image and manifest-bound physical workloads remain separate from older
release artifacts. The Windows host embeds matching stock/C11/C12 payloads;
actual-PE Wine sessions cover boot, NetDisk, A: snapshots, mounting B:, captures
and host-event conversion to JSON. They do not require a B: read. This conversion
does not independently decode
the RX/TX protocol frames; see
[capture conversion](portable-c-host-implementation.md#capture-conversion).
See [Windows qualification](windows-jukuhost-client-implementation.md)
for the platform boundary.

The focused CS00000 results above do not complete broader release-profile
qualification on the corrected pair. Real Windows serial hardware also needs
its own lifecycle and endurance qualification; Wine is not evidence for that
boundary.

The older production-Linux-host stress extension is not a passing C12 gate:
it accumulated seven modeled USART overruns and missed the final warm-boot
prompt. Dedicated C12 CP/M and bounded Wine gates have different timing scopes;
their passes do not establish that stress workload or physical endurance.

## Verification commands

From this repository, rebuild and compare all named ROM artifacts and run the
C-model and focused structural gates:

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py --check
sync/network_first_rom_abi_check.sh
sync/network_first_rom_hdl_check.sh
```

From the sibling `cpm-plus-juku`, `make c12-check` verifies matching CP/M
integration and `make c12-simulator-candidate` produces the reproducible
non-physical package. None of these commands proves broader physical
qualification or authorizes new programming.
