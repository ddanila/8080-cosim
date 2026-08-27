# JukuNet C9 ROM plan

Status: **PHYSICALLY EVALUATED; CORE PATHS PASS, LOCAL VIDEO DEFECT FOUND;
NOT PROMOTED**.

Decision date: **2026-08-26**

Physical closeout date: **2026-08-27**

The exact named C9 pair was subsequently programmed and evaluated on CS00000.
Its network boot, CP/M, N4, disk, write, diagnostic, warm-boot, recovery, and
host-replacement paths passed, but local video remained blank despite sync.
An exact EKTA-style `0Eh` PPI0 BSR write restored video immediately in the
running C9 session. C9 is therefore frozen as physical evidence and is not a
promotion candidate. The proved correction and follow-up gates are recorded
in [`network-rom-c10-plan.md`](network-rom-c10-plan.md).

C8 (`juku-network-rom-abi1.3-c8.bin`) is immutable and remains the qualified
baseline. C9 is a separately named successor whose purpose is to make the
resident N4 console path observable and unable to stall the authoritative
local console, while adopting the already-recorded unconditional network-boot
policy. This plan authorizes the separately named simulator/HDL candidate and
its reproducible package; it does not authorize EPROM programming or physical
promotion.

## Qualified implementation result

The C9 implementation completed on 2026-08-26 as a separately named ABI 1.4
candidate. It does not modify C8. The original missing-output observation did
not reproduce on the exact native C8 production path: both the retained C8
gate and its machine-readable capture contain ordered operation `21h` output.
No speculative emission workaround was added. The unresolved physical-session
difference is therefore treated as host/session configuration evidence to
collect during physical acceptance, not as proof of a C8 ROM defect.

C9 implements the independently justified hardening in this plan:

- transmitter polling is bounded to 8,192 polls per byte, receive polling to
  65,535 polls per byte, and reply-prefix scanning to 256 received bytes;
- ABI 1.4 publishes the retained failure/reconnect prefix plus negotiation
  flags and the failed operation, with distinct reasons `00h..06h`;
- failed N4 output returns to the authoritative local console, while a later
  input poll can reconnect without RESET;
- S21 bit 0 is reserved and network boot is unconditional; all 16 combinations
  of bits 4:1 retain their video and character-bank behavior;
- the C9 CP/M profile preserves the `0100h..9BFFh` TPA and exposes the new
  fields through `STATUS` 1.4; and
- `vc8080` consumes the production N4 PTY with simulator output interception
  explicitly disabled.

The focused fault matrix measured a worst bounded return of 1,562,211 emulated
8080 cycles. The broad C-model gate, structural HDL gate, CP/M local/remote
gates, native C host gate, host-replacement gate, C8 compatibility matrix, and
a real headless `vc8080` smoke all pass. The native C9 capture contains
NetDisk-v3 read/write, N4 output, time, status, diagnostic and warm-boot
publication operations.

Deterministic candidate identities are:

- combined ROM: `352417fafcf1ceaef40b8d39916acdaee6de03d914eafe2b54185ccbabe35530`;
- D15 low half: `b18e96e8f4cc88c7436e457b63b564ad42e1bf55f3e997f272301096c463593e`;
- D16 high half: `6f9bdf53bcf7ee919224305bcaf135c2d0076779218f49a2aed5395dc6baf932`;
- CP/M system: `ec06111e197a75a628d6a8c917542d0afa68c66ac26d14d39b9ef13aa0b38225`;
- Fastboot V16: `cae64165a04837d309f7b02c88a25754186ec333166ab5dd725d6e178088761b`;
- C9 full volume: `26f640ea6f0f7237910731f56ae006944d9102d51bfe5d217c4025a78d9fed10`;
  and
- non-physical candidate archive: `43b03802e156dba0492c860fe27a9fc1aec1672cf5dc0afab82176fbd243eb75`.

These results authorize keeping and testing the C9 candidate artifacts only.
They do not authorize burning D15/D16; the physical gates below remain open.

The complete `make c9-simulator-candidate` target also passes from empty
build/output directories in isolated clean source snapshots. The retained log
is `cpm-plus-juku/out/c9-simulator-candidate-cleanroom-20260826.log`, SHA-256
`5c81086f7d5bd22365faf42b78b5035259abf7e73366e173f037f1b938619ddb`;
both source snapshots remained clean after the run.

## Goals

1. Explain and correct the physical/model discrepancy in resident N4 console
   output. A correction must be based on a reproduced cause, not merely on the
   assumption that operation `21h` is absent from the ROM.
2. Bound every phase of a resident host transaction, including transmitter
   readiness and synchronization through malformed continuous input.
3. Publish enough stable host state to identify negotiation and transport
   failures without an instrumented ROM or a working local display.
4. Make network boot unconditional and reserve S21 bit 0, while retaining the
   existing meanings of S21 bits 4:1.
5. Preserve C8's TPA, local-console authority, protocol compatibility and all
   earlier fixed ABI entry points.

## Baseline evidence and unresolved discrepancy

One instrumented C8 session, paced at 1.7 MHz and serving 1,677 NetDisk
requests, observed the resident host argument byte receive the complete CP/M
banner and prompt but observed no console-output operations. The host capture
contained operation `20h` console polls and operation `26h` capability
negotiation, but neither `21h` byte output nor `28h` block output. The
capability response advertised N4 console support.

That observation does not by itself prove a missing C8 ROM implementation.
On 2026-08-26 the exact native Linux production-host gate passed:

```text
JUKUHOST-C8-COSIM-TEST: PASS (C8 V16 -> N3/N4 -> DIR)
```

`tests/jukuhost_c8_cosim_test.py` uses the named C8 ROM and matching CP/M
system, configures no simulator CONOUT hook, receives the banner and `A>`
through `jukuhost --console-pty`, enters `DIR`, and receives its output through
N4. The working native modeled path and the no-output instrumented path must
therefore be compared before C9's console change is selected.

The investigation must record, for both paths:

- the exact ROM, D15/D16, CP/M system, Fastboot and host identities;
- the N3/N4 readiness marker and capability bytes;
- transitions of `RHPRES`, `RHEN`, `RHBACK`, `RHOP` and `RHINPUT`;
- calls through `NCOUT`, `JCGHOST` selector `JROMHOSTOUT`, and the resulting
  `20h`, `21h`, `26h` and `28h` requests;
- D11 status and the timing of any host enable, failure and recovery event.

The accepted fix must address the first demonstrated divergence. A model-only
or host-platform fault is fixed in that layer; C9 must not accumulate a ROM
workaround whose triggering condition is unexplained.

## C9 resident-host contract

### Best-effort N4 output

When N4 is negotiated and the advertised console capability is enabled, every
character accepted by the CP/M console-output path must remain visible locally
and be eligible for ordered N4 mirroring. The local display and physical key
matrix remain authoritative. Host loss, malformed traffic or a failed USART
must never prevent or indefinitely delay local output.

Operation `21h` is the correctness baseline. Existing operation `28h` may be
used when a caller already supplies an ordered span of 1..32 bytes. A new
persistent output buffer is not part of the baseline: C8 uses 27 bytes at
`D7E0h..D7FAh`, and only `D7FBh..D7FFh` remains in that end-of-workspace
envelope. Buffering is admitted only after a measurement demonstrates a useful
gain and proves ordering and flush behavior for newline, input, disk traffic,
warm boot and host loss without reducing TPA.

After a host failure, output remains local-only. A bounded, infrequent
reconnect probe during continued output may be added if testing shows that it
recovers a useful part of long command output without imposing a visible
local-console delay. Recovery at the established console-input polling point
remains required.

### Completely bounded transactions

The existing receive wait has a finite counter, but `rh_tx_wait` waits without
a limit for D11 transmitter readiness. The synchronization loop is also only
bounded per received byte and can run forever if a continuous stream never
contains a valid reply prefix. C9 must give the complete transaction a finite
cycle/iteration budget covering:

- every transmitter-ready wait;
- reply-prefix scanning, including continuous garbage;
- header, body and checksum reception;
- sequence and status validation;
- drain/resynchronization and retry;
- failure backoff and any reconnect probe.

Every exit must restore the documented USART mode, memory mode, stack and
caller-visible registers. Exhausting any budget disables the remote path,
records a reason, and returns control to the caller. In particular, CONOUT
must have a measured worst-case bound with a silent host, stuck TX-ready bit,
continuous garbage, truncated reply and corrupt reply.

### Failure and negotiation telemetry

C8's two-byte public host state contains a generic nonzero last-failure value
and a saturating reconnect count. C9 should retain those first two fields and
replace the generic value with a documented nonzero reason enum. At minimum it
must distinguish:

- transmitter timeout;
- receive timeout;
- synchronization/framing budget exhaustion;
- sequence mismatch;
- checksum/reply-integrity mismatch;
- rejected or unsupported host status.

The C9 status contract must also expose, directly or through flags derived from
existing state, whether the host was detected, N4 was selected, console
capability was advertised, mirroring is currently enabled, and a reconnect has
occurred. `STATUS`, host logs and the machine-readable capture decoder must use
the same names and values.

If new externally visible fields or selectors are published, C9 becomes ROM
ABI 1.4. It must append through the existing selector dispatch where possible,
retain every ABI 1.0--1.3 vector address and calling convention, and keep the
first two host-state bytes useful to ABI 1.3 callers. The copied low-RAM gate
must not be enlarged merely to obtain another direct vector.

## Unconditional network boot

C9 always attempts network boot after bounded POST. S21 bit 0 is reserved and
has no C9 behavior. Both values of bit 0 must follow the same boot path and
produce the same host protocol, apart from raw-switch telemetry if that byte is
reported.

S21 bits 2:1 continue to select 40x24, 53x24, 64x20 or 80x24 video, and bits
4:3 continue to select English, Estonian, CP866 Russian or English/user-remap.
Bits 7:5 remain reserved. C8 retains its concealed `N` gate unchanged.

The unconditional policy must remove obsolete wait code where practical; it
must not silently reassign bit 0 to a recovery mode or another feature. A
future reuse requires its own user-visible, operationally distinct proposal.

## Memory and compatibility constraints

- Rebuild C4, C5, C6, C7 and C8 byte-identically before accepting C9.
- Preserve the C8 transient span `0100h..9BFFh`, 39,680 bytes.
- Keep the ROM gate/work reservation at `D600h..D7FFh` and audit every byte of
  any use of `D7FBh..D7FFh` against all console, NetDisk, diagnostic, warm-boot
  and interrupt paths.
- Retain 19,200 baud and the existing N3/N4 and NetDisk-v3 wire contracts.
- Preserve local display and keyboard behavior when the host is present,
  absent, slow, malformed, disconnected or restarted.
- Keep C8's complete-ROM diagnostic, D57/D11 diagnostics, POST state and
  audible C1--C5 failure codes.
- Generate a distinct `JukuNet C9` identity and deterministic combined,
  D15-low and D16-high images. Never rebuild modified bytes under a C8 name.

## Implementation sequence

1. **Close the discrepancy.** Re-run the native C8 no-hook gate, reproduce the
   no-output path with exact artifact identities, and trace the first divergent
   state or call. Record whether the correction belongs in ROM, CP/M binding,
   simulator, host or physical serial configuration.
2. **Add failing recovery fixtures.** Before changing the transport, inject
   stuck transmitter, silent receiver, continuous garbage, truncated reply,
   wrong sequence, bad checksum/status and host restart during output. Assert a
   finite return and uninterrupted local output.
3. **Implement the smallest correction and transaction deadline.** Preserve
   all C8 calling conventions and validate worst-case cycle counts. Establish
   correct ordered operation `21h` output before considering bulk optimization.
4. **Publish telemetry.** Define the reason enum and flags, update ABI metadata
   if required, and update CP/M `STATUS`, host logs and capture decoding.
5. **Apply unconditional boot.** Remove the S21-bit-0 gate and prove all other
   S21 combinations remain unchanged.
6. **Qualify and package.** Run the complete simulator/model/HDL/CP/M matrix,
   produce reproducible candidate artifacts and review their maps and hashes.
   Physical programming requires a separate explicit decision after these
   gates pass.

Steps 1--6 are complete for the simulator/HDL candidate. The physical gates
below remain deliberately open.

## Acceptance gates

### Automated

- `python3 tests/jukuhost_c8_cosim_test.py` remains a passing immutable-baseline
  check and the corresponding C9 gate obtains prompt and command output only
  from `--console-pty`.
- The C9 gate proves ordered console output and input, `DIR`, `VER`, warm boot,
  TIME, STATUS, diagnostics, A:/B: NetDisk traffic, writes and host replacement
  without a simulator CONOUT hook.
- Fault injection proves finite CONOUT return for stuck TX, silent RX,
  continuous garbage, short reply, wrong sequence, bad integrity/status and
  disconnect during output. Each path publishes the expected reason and
  subsequently reconnects without RESET.
- A local-only run produces the same visible bytes and remains responsive with
  no host throughout boot and CP/M operation.
- Both S21-bit-0 values boot identically; all video-mode, character-bank,
  keyboard and remap fixtures for bits 4:1 retain their C8 results.
- the `vc8080` live runner removes the temporary `JUKU_CONSOLE_OUT_PC`
  dependency and consumes the production N4 console path. Its separate legacy
  C7 system-matrix harness may retain simulator observation because it also
  validates physical-key debouncing through the same PTY; it is not a C9
  runtime dependency.
- C4--C8 artifact hashes remain exact, the C9 build is deterministic, D15
  followed by D16 equals the combined image, the ROM/ABI map has no overlap,
  and C9 preserves `0100h..9BFFh`.

### Physical

Record any authorized bench session in the prepared
[`c9-physical-acceptance-worksheet.md`](../../cpm-plus-juku/docs/c9-physical-acceptance-worksheet.md).

- Program and built-in-verify named C9 D15/D16 candidates only after automated
  acceptance and explicit programming approval; record programmer CRC/SHA-256,
  board identity, switch byte and supply measurements.
- On CS00015, capture a complete cold-boot prompt and command transcript only
  through `jukuhost --console-pty`; exercise host loss and replacement without
  RESET and verify the new failure/reconnect telemetry.
- On a Juku with a usable display path, compare the local and N4 transcripts
  character for character and demonstrate that disconnecting or corrupting the
  host does not freeze local output.
- Repeat the C8 blind boundary: keyboard input, A:/B:, TIME, STATUS, DIAG,
  write/readback, warm boot, long output, disk soak and normal sound, with zero
  clean-path transport errors.

## Deferred work and non-goals

The following do not enter C9 without a separate measured justification and
scope decision:

- runtime `CONSOLE MODE` and `CONSOLE CHARSET` switching; it remains a C9-or-
  later ABI proposal but multiplies the physical video qualification matrix;
- baud rates above the physically proven 19,200 setting;
- a persistent N4 output buffer or output compression;
- a new NetDisk protocol, speculative read predictor or unprofiled cache;
- write-back caching or any power-loss exposure;
- cryptographic boot authentication;
- banked CP/M, XMODEM or unrelated distribution utilities;
- attempting to repair CS00015's board-local pixel-output fault in ROM;
- new POST tests before the retained C8 display and induced failure-tone
  observations are closed or explicitly waived.

These exclusions keep C9 centered on one observable console/recovery boundary,
one transport-hardening change and the already-approved boot-policy cleanup.
