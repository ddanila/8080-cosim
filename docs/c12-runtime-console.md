# C12 runtime console and improvement ledger

Status: **CORRECTED CP437, WARM/DEFAULT, RESET AND POWER-CYCLE CHECKS
PASSED ON CS00000; BROADER RELEASE QUALIFICATION SEPARATE**

## 2026-09-05 physical finding and correction

CS00000 booted the original C12 pair and passed cold STATUS/DIAG. The owner
confirmed stable, correct 40x24 English, 53x24 Estonian, and 64x20 Russian
VIDTEST pages. The 80x24 user/remap page displayed question marks instead of
DAh/D9h corner glyphs. That page failed visual acceptance; the attended run
was stopped without confirming it or proceeding to RESET/power-cycle tests.
The retained CP/M session is
`out/physical-CS00000-c12-runtime-attended-20260905`; its host stopped with
zero disk retries and UART errors. S21 was read as 0F.

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

The owner explicitly authorized the corrected D16 write. DOSRAVI session
`at28c64-jukunet-c12-cp437-d16-write-20260905` records two changed bytes,
8,192 verified bytes, no retries, CRC32 B54EE486, and VCC/VPP off. D15 was
retained. The owner fitted D16 and confirmed the startup checkerboard.

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

The sibling CP/M acceptance fixtures now declare their C11 manifest dependency,
use explicit resumed-session STATUS expectations, and check CONSOLE's two
override lines independently. Byte-exact original CS00000 transcripts are
retained under `tests/fixtures/c12-CS00000-20260905/` for offline replay and
negative tests. Cold-state and hardware-error checks remain strict.

C12 is an additive successor to the immutable C11 ROM. It implements the one
fully specified, hardware-compatible improvement left in the retained design
record: switching video geometry and character bank at runtime without using
S21 or resetting the machine. It also gives the inherited passive boot beacon
a C12 identity so a host can report which ROM is waiting.

## ABI 1.5 contract

Feature bit `1000h` and vector `FF5Fh` identify `JCGCONCONFIG`:

| A | Operation | Inputs | Successful result |
| ---: | --- | --- | --- |
| 0 | query | none | A=reset-latched S21, B=active mode, C=active bank, D=override flags |
| 1 | set | B=mode 0..3, C=bank 0..3 | applies the complete pair, A=0/CY clear |
| 2 | default | none | reapplies S21 bits 4:1, A=0/CY clear |

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

The assembler now fails closed at every fixed resident-ROM envelope instead
of relying on a negative padding expression when C12 consumes older diagnostic
slack. The generated metadata records 154 bytes after resident diagnostics,
839 after the locale console, 896 after the resident host, and 158 after the
ABI vectors. These are padding measurements, not permission to append another
ABI vector: the corresponding low-RAM call-gate envelope is exactly full.

## Boot discovery identity

C12 retains C11's passive, receive-only recovery behavior but emits checked
frame `4A 42 0C 01 05` (`JB`, C12, flags 1, XOR 5). C11 continues to emit its
byte-identical `JB/11` frame. The production host accepts both identities and
logs the received ROM generation; random or malformed data does not select a
boot path.

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

The owner authorized and installed the corrected pair on 2026-09-05. Focused
physical results and their exact scope are recorded above; broader release
promotion must distinguish the original and corrected images.

## Improvement disposition

Included in C12 because the contract and evidence are complete:

- atomic runtime video geometry and character-bank switching;
- separately observable S21 default, active pair, and override flags;
- warm-boot preservation and explicit default restoration;
- runtime-switch preservation of the existing persistent key-remap table;
- distinct `JB/12` discovery identity with C11-compatible host recovery;
- deterministic artifacts and exhaustive simulator regression.

Completed above the ROM core:

- CP/M `CONSOLE` query/set/default control plus STATUS/DIAG active-state and
  independent-override reporting;
- distinct C12 system, Fastboot, and 400 KiB release-image artifacts;
- C12-specific `VIDTEST` reads the active ABI 1.5 tuple, with exact switched
  framebuffer proof while all older release binaries remain unchanged;
- manifest-bound cold/runtime/full physical profiles and an exact CS00000
  worksheet covering every geometry and character bank;
- Windows-host C12 selection with six embedded stock/C11/C12 payloads;
- actual-PE Wine boot, NetDisk, snapshot, B:, capture, and evidence decoding
  for stock, C11, and C12.

Still required before calling C12 physically complete:

- any broader release-profile rerun on the corrected pair beyond the focused
  CS00000 glyph and lifecycle checks recorded above;
- physical Windows-to-CS00000 qualification remains a separate host-product
  gate and is not inferred from Wine.

A supplemental attempt to add C12 to the older, long production-Linux-host
stress workload reached ABI/default-state reporting, diagnostics, disk reads,
and journaled writes, but the simulator accumulated seven USART overruns and
missed the final warm-boot prompt. The dedicated C12 CP/M gate passes the same
warm-boot behavior, while the bounded actual-PE Wine C12 run has zero retries
and UART errors. The stress extension is therefore recorded as a timing-fixture
follow-up, not committed as a flaky release gate and not treated as physical
evidence.

Not folded in without new evidence or a separate design decision:

- write-back disk caching, because power-loss semantics are unsafe;
- cryptographic boot authentication, because its 8080/EPROM/wire cost is not
  yet measured;
- higher serial rates, whose physical margin is unproved;
- RAM banking, which requires hardware support;
- XMODEM or host-side filesystem shortcuts that duplicate the authenticated
  bootstrap/NetDisk path;
- repurposing S21 bit 0 without a concrete distinct behavior.

## Completion audit

This table is the finite acceptance boundary for “C12 implemented with all
currently justified improvements folded in.” A pass requires direct evidence;
an unmeasured idea is dispositioned above rather than silently becoming a
release requirement.

| Requirement | Authoritative evidence | State |
| --- | --- | --- |
| Deterministic D15/D16 pair | generator check, split/concatenation test, additive checksums, exact hashes above | pass |
| ABI 1.5 layout and compatibility | exact 224-byte gate, `1000h` feature, `FF5Fh` vector, immutable C4--C11 regressions | pass |
| Complete runtime selection | independent framebuffer/font oracle for all 16 mode/bank pairs | pass |
| Atomic failure and transition policy | invalid selector/value fixtures, full-raster-tail checks, cursor/timing reset, published state checks | pass |
| Keyboard transition safety | pending/debounce state discarded and installed four-pair remap retained across set/default | pass |
| Warm/default lifecycle | local and N4 CP/M switch, `WBOOT`, STATUS/DIAG, and `CONSOLE DEFAULT` checks | pass |
| Active visual utility | C12-only strict-8080 VIDTEST build plus exact switched 40x24/Russian hidden/visible frames; legacy hash retained | pass |
| Structural hardware model | VM80A/Juku ABI self-test with POF release, runtime transition, remap, keyboard, and serial completion | pass |
| Host delivery | reproducible PE, six pinned payloads, actual-PE stock/C11/C12 Wine sessions | pass |
| ROM capacity fail-closed | assembly envelope assertions and generated padding measurements; ABI call gate exactly full | pass |
| Reproducible physical procedure | manifest-bound workloads, captured original failures, corrected fixtures and audited focused rechecks above | executed in the recorded focused scope |
| Installed-hardware behavior | three original-pair visual modes; corrected-pair CP437, warm/default, reset and power-cycle evidence above | focused checks pass; broader release qualification separate |
| Real-Windows serial product | current Windows, real PL2303 and CS00000 lifecycle/endurance evidence | separate host-product gate |

The first ten rows close every C12 implementation and desk-verification item.
The ROM cannot be called physically complete until the installed-hardware row
passes. The last row does not change C12 ROM readiness: it qualifies the
Windows distribution and driver boundary separately.
