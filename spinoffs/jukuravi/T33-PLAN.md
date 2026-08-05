# T33 plan: serial-only A12 discrimination on CS00015

Status: **PLAN / NOT YET EXECUTED**

Everything below runs against the already-burned T32 ROM
(`firmware/diag-d0-waitclass.bin`, SHA-256
`61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2`)
through loader API v2 over the existing X3 serial path. No re-burn, no board
rework, no instrumentation. Expected bytes quoted below were extracted from
that exact image, and every planned cell was checked to discriminate: the
correct second byte differs from the A12-low-aliased second byte in all cases.

Context: [`T32-PHYSICAL.md`](T32-PHYSICAL.md) established that isolated
upper-D15 reads are correct while the second uninterrupted read in the `1Axx`
and `DAxx` classes behaves as physical-A12-low, in ROM and all-RAM modes
alike, with `4Axx/5Axx` passing. The probes below complete the logical
signature of that fault. Component-level attribution (D1 versus D4 versus
conductor/load) is explicitly out of scope: it is not reachable from software
and ends at the scope/donor-board steps already listed in T32.

Session hygiene: boot fresh before each numbered probe, log every run under
`sessions/t33-<probe>-<case>/`, and commit all sessions afterwards, including
failures. Each probe below states its full command lines; run them from the
repository root on the lab machine.

## 0. Preconditions

```sh
bash sync/jukuravi_t32_check.sh          # image + probe suite still bit-exact
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --expect-rom-version 1B --expect-crc16 D62B \
  --log-dir spinoffs/jukuravi/sessions/t33-boot
```

A clean `1B/D62B` boot with the loader resident is the entry condition for
every probe. If the boot itself fails, stop and record; nothing below is
interpretable without it.

## 1. Alias-regions probe (already written; closes the `9A` cell)

`firmware/ram-a12-alias-regions-4000.asm` is committed and cosim-guarded but
has no physical session. It seeds distinct target and alias bytes in all four
`A15:A14` classes in all-RAM mode, then samples isolated and consecutive
reads. Result block: 60 bytes at `4400h` (`"A12M"`, count, `A5h` completion,
four 13-byte class records for `1A/5A/9A/DA`).

```sh
nasm -f bin -o /tmp/t33-alias-regions.bin \
  spinoffs/jukuravi/firmware/ram-a12-alias-regions-4000.asm
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --load /tmp/t33-alias-regions.bin --load-address 4000 \
  --run-address 4000 --run-mode call \
  --result-address 4400 --result-length 60 \
  --log-dir spinoffs/jukuravi/sessions/t33-alias-regions
```

| `9A` record shows | Interpretation |
| --- | --- |
| aliased second bytes | failing classes are exactly `A15==A14` — the D8/`ROM_SEL` `Q` geometry; strong structural clue even though D8 substitution changed nothing |
| correct pairs | the `Q` symmetry dies; `A14` alone separates pass (`A14=1`) from fail (`A14=0`) |

This probe also re-verifies `1A`/`DA` fail and `5A` pass with deliberately
seeded aliases, upgrading T32's "unified, exact hypothesis" to a proof.

## 2. Wait-class read-pair matrix (does a WAIT rescue the second read?)

T32's `1100/1200/1400` matrix was execution-only, where operand aliasing kills
every class indistinguishably. Read pairs per D2 wait class have never been
measured. `firmware/rom-read-pair-4000.asm` takes the target on the nasm
command line; result block: 42 bytes at `4100h` (`"PAIR"` header, target,
expected pair, `SAMPLE_COUNT=16`, then 16 sampled pairs).

Run once per row, fresh boot between rows:

```sh
nasm -f bin -DTARGET=0x1000 -DEXPECTED0=0x00 -DEXPECTED1=0xC0 \
  -o /tmp/t33-pair-1000.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -DTARGET=0x1100 -DEXPECTED0=0x3E -DEXPECTED1=0x11 \
  -o /tmp/t33-pair-1100.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -DTARGET=0x1200 -DEXPECTED0=0x3E -DEXPECTED1=0x12 \
  -o /tmp/t33-pair-1200.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -DTARGET=0x1400 -DEXPECTED0=0x3E -DEXPECTED1=0x14 \
  -o /tmp/t33-pair-1400.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm

# for each image:
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --load /tmp/t33-pair-<case>.bin --load-address 4000 \
  --run-address 4000 --run-mode call \
  --result-address 4100 --result-length 42 \
  --log-dir spinoffs/jukuravi/sessions/t33-pair-<case>
```

| Target | D2 class | Correct pair | Aliased second byte reads |
| --- | --- | --- | --- |
| `1000h` | CAS-gated | `00 C0` | `0B` (from `0001h`) |
| `1100h` | CAS-gated | `3E 11` | `17` (from `0101h`) |
| `1200h` | no wait | `3E 12` | `02` (from `0201h`) |
| `1400h` | always wait | `3E 14` | `E6` (from `0401h`) |

Interpretation. If `1400h` (always wait) returns the correct pair while
unwaited classes alias, the READY/D30 timing hypothesis (T32 alternative 2)
gains hard support: an inserted WAIT rescues the second cycle. If all classes
alias identically — which the all-RAM result already hints at — that
hypothesis is effectively dead and the weight moves to D1/D4 dynamic address
behaviour. The wait-class map is derived and guarded in
[`../../docs/d2-ready-cycle-analysis.md`](../../docs/d2-ready-cycle-analysis.md);
note its caveat that the D2 address-pin order rests on solder-fit evidence, so
treat "class" here as *page geometry*, which is measured, not as a verified
wait count.

## 3. Rise-versus-hold boundary pairs

Same source, boundary targets. `LHLD 0FFFh` makes A12 *rise* between the two
consecutive reads; `LHLD 1FFFh` makes it *fall* (second read `2000h` is
unpopulated D16, so its value is open-bus and only the first byte is judged):

```sh
nasm -f bin -DTARGET=0x0FFF -DEXPECTED0=0x21 -DEXPECTED1=0x00 \
  -o /tmp/t33-pair-0fff.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
nasm -f bin -DTARGET=0x1FFF -DEXPECTED0=0x76 -DEXPECTED1=0xFF \
  -o /tmp/t33-pair-1fff.bin spinoffs/jukuravi/firmware/rom-read-pair-4000.asm
```

| Result at `0FFFh` pair | Interpretation |
| --- | --- |
| `21 00` (correct) | A12 *can* rise on an immediately following read; the fault is holding/keeping it high — points at droop/load or a release edge |
| `21 C3` (`0000h` content) | A12 cannot assert on the second consecutive read at all — points at the driving side (D1/D4) |

This cell is the sharpest single discriminator in the plan.

## 4. History dependence (the unexplained trampoline asymmetry)

T32 measured `4000h -> JMP 1A00h` leaving the marker untouched (`D5h`) but
`5A00h -> JMP 1A00h` writing `01h`, deterministically, twice. The current
cosim model (`JUKU_CONSECUTIVE_A12_LOW_PAGES`, `cosim/trace.c`) is page-local
and history-blind, so it predicts identical markers for both — the model is
known-incomplete and the trigger has an address-history component.

Formalize with the *same* read-pair code relocated so that its own instruction
fetches set the address history. `rom-read-pair-4000.asm` is assembled at
`org 04000h` with absolute internal references, so relocation needs a one-line
`BASE` parameter added to the source (mechanical: replace the four absolute
`dw` references to `RESULT`/`sample_loop` origins with `BASE`-relative values;
keep the default `BASE=04000h` so the existing T32 regression is unchanged).
Then run the identical `TARGET=0x1A00` probe from three placements:

| Code placed at | Fetch history before each `LHLD 1A00h` | Expect if history-blind | Expect if A12-high history matters |
| --- | --- | --- | --- |
| `4200h` | `A12=0` fetches | first byte `3E`, second aliased `43` | same |
| `5A00h` | `A12=1` fetches, passing class | same as above | first byte may alias too |
| `9A00h` | `A12=1` fetches, class under test from probe 1 | same as above | code itself may misfetch — record whether the probe even completes |

`9A00h` is inside loader RAM (`4000h-BFFFh`), so placement is a plain
`--load-address 9A00 --run-address 9A00`. If the probe run from `9A00h`
corrupts or fails to return, that is itself a first-class result: record the
session and re-attach; do not retry blind.

## 5. Write-cycle extension (all-RAM mode only)

All T32 evidence is read-side. Whether consecutive *writes* also drop A12
splits the mechanism: writes have no DBIN/READY read-latch involvement, so if
they alias too, the fault is purely the address path (D1/D4/BA12 load) and the
read-latch/READY story is finished. If writes never alias, the fault
correlates with read cycles specifically.

Safety rule: never aim a write probe at the ROM window in mode 0. The fitted
AT28C64B is electrically writable and the socket's write gating is unverified.
Do write tests in all-RAM mode (mode 3) or in plain RAM classes only, reusing
the PPI mode-switch prologue/epilogue from
`firmware/rom-overlay-source-4000.asm` (configure PPI #0 PC3..PC0, select
mode, restore reset directions before RET).

New small sources, T32 db-style, each with a cosim regression before the lab
session (the cosim `JUKU_CONSECUTIVE_A12_LOW_PAGES` model currently faults
reads only, so clean-model runs define the pass baseline):

- `ram-write-pair-4000.asm`: seed sentinels at `DA00h/DA01h` and at the alias
  `CA00h/CA01h`; `LXI SP,DA02h` + `PUSH B` performs two consecutive writes
  (`DA01h` then `DA00h`); restore SP, read back all four bytes into the result
  block. Second write landing at `CA00h` = writes alias.
- `ram-rmw-4000.asm`: `INR M` with `HL=DA00h` (read-then-write at one
  address); readback of `DA00h` and `CA00h` shows where the increment landed.

Both report through the standard `4100h` result block so the existing host
command shape works unchanged.

## 6. Confirmations and soak (cheap, run if time remains)

- `ram-pop-pair-4000.asm`: `LXI SP,1A00h` + `POP H` — the same consecutive
  pair through stack-status read cycles. Expected: aliases identically,
  confirming the 8080 status word is irrelevant (consistent with the desk
  result that nothing on this board consumes cycle type).
- Soak: loop the `TARGET=0x1A00` pair probe for several minutes via repeated
  CALLs, counting mismatching pairs, cold and after warm-up. 16/16 aliased
  every round = hard fault; any drift = marginal/thermal.

## 7. Desk follow-up (no bench required)

Refine the cosim fault model until it reproduces *every* retained session
bit-exactly: the `D5h/D5h/01h` trampoline markers, all read-pair tables, and
T31's `106Fh` tone path. Candidate triggers to encode and test against the
probe-3/4 results: same-page consecutive counter (current model), consecutive
A12-high run length, reset-on-write, reset-on-opposite-A12-access. Each
predicts different outcomes for the matrix above, so one bench session plus
model iteration should converge. Acceptance: a single env-var model under
which cosim replays of every retained T32/T33 probe match the physical bytes.

## Decision tree summary

```text
probe 1 (9A cell)      -> Q=(A15==A14) geometry vs plain A14 split
probe 2 (wait matrix)  -> READY/D30 timing vs D1/D4 dynamic path
probe 3 (0FFF rise)    -> cannot-rise (driver side) vs cannot-hold (load/droop)
probe 4 (placement)    -> history term for the model; 9A00h execution result
probe 5 (writes)       -> address-path fault vs read-cycle-specific fault
```

After these, software is exhausted in the strict sense: the remaining
alternatives are electrically indistinguishable from the bus, and the next
steps are T32's scope comparison at `D1.37` versus `D4.15/BA12` and the
same-chip donor-board run.
