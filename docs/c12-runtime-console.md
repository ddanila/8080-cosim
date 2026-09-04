# C12 runtime console and improvement ledger

Status: **ROM, CP/M CONSUMER, HOST PAYLOAD, AND LOCAL WINE E2E IMPLEMENTED;
PHYSICAL ACCEPTANCE PENDING**

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

- combined: `724f672657390882f10c19588778527bd0b46848616ccf4ec348502dbb36e18b`;
- D15 low: `b95eb5b0842d501ee602d82a7907b1cf4baf3e1b2cd74f73ef553eac60faf9de`;
- D16 high: `45193e069ee3dca7a0abf98a20a563959c2a760e9eca828659d69a76420fe9b4`.

`sync/network_first_rom_hdl_check.sh` also runs the C12 ABI self-test through
the structural VM80A/Juku model, including call-gate dispatch, POF release,
runtime transition, retained remap, translated keyboard input, and serial
completion. The exhaustive 4x4 framebuffer oracle remains in the faster
C-model matrix.

These are not yet authorized as a burn pair. The focused visual/runtime switch
matrix must pass on CS00000 before physical promotion.

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

- attended CS00000 runtime visual switching and reset/default checks;
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
| Reproducible physical procedure | manifest-bound cold/runtime/full workloads and exact CS00000 programming/rollback worksheet | ready, not executed |
| Installed-hardware behavior | attended CS00000 four-mode/four-bank raster, recovery, warm/default, reset and power-cycle evidence | pending |
| Real-Windows serial product | current Windows, real PL2303 and CS00000 lifecycle/endurance evidence | separate host-product gate |

The first ten rows close every C12 implementation and desk-verification item.
The ROM cannot be called physically complete until the installed-hardware row
passes. The last row does not change C12 ROM readiness: it qualifies the
Windows distribution and driver boundary separately.
