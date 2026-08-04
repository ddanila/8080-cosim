# D2 READY wait classes and the A12 fetch/read premise

Status: **DESK ANALYSIS / FETCH-SELECTIVE PREMISE NOT SUPPORTED**

This generated report re-derives, from the validated D2 `.037` READY PROM,
what wait treatment each page of the D15 window receives, and then asks
whether the CS00015 "A12 problem" as framed in
[`../spinoffs/jukuravi/T31-PHYSICAL.md`](../spinoffs/jukuravi/T31-PHYSICAL.md)
is physically expressible. It adds no measurement; it only draws out what
the already-preserved tables imply.

## Provenance

- Raw D2 image: `ref/physical-proms/validated/d2_037.raw.bin`, SHA256 `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`
- Input order (from `docs/d2-reconstruction-constraints.md`):
  `{WREQ_N, A10, IORC_N, A14, CAS, A9, A15, A12}`
- Raw `0` sinks `READY_D`; raw `F` releases it to the R6 pull-up.
- Memory-cycle assumption: `WREQ_N=1` (D6.11 `RAM_SEL` inactive, so not a
  DRAM access) and `IORC_N=1` (not an I/O read). `hdl/juku_top.v` wires the
  PROM as `{wreq_n, A[10], iorc_n, A[14], cas_n, A[9], A[15], A[12]}`, so the
  table's `CAS` bit is the active-low `cas_n` rail.

Naming note: `docs/d2-physical-truth.md` calls pin 2 `XACK_N` while
`docs/d2-reconstruction-constraints.md` and the HDL call it `IORC_N`. The
constraints file proves these are the same conductor (`-XACK` and `-IORC`
labels at the identical factory edge coordinate 106C), so this is an alias,
not a conflict.

## Wait class per page of the D15 window

| Page | A12 | A10 | A9 | `cas_n=0` | `cas_n=1` | Class |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `0000-00FF` | 0 | 0 | 0 | release | release | no wait |
| `0100-01FF` | 0 | 0 | 0 | release | release | no wait |
| `0200-02FF` | 0 | 0 | 1 | release | release | no wait |
| `0300-03FF` | 0 | 0 | 1 | release | release | no wait |
| `0400-04FF` | 0 | 1 | 0 | sink | sink | always wait |
| `0500-05FF` | 0 | 1 | 0 | sink | sink | always wait |
| `0600-06FF` | 0 | 1 | 1 | sink | sink | always wait |
| `0700-07FF` | 0 | 1 | 1 | sink | sink | always wait |
| `0800-08FF` | 0 | 0 | 0 | release | release | no wait |
| `0900-09FF` | 0 | 0 | 0 | release | release | no wait |
| `0A00-0AFF` | 0 | 0 | 1 | release | release | no wait |
| `0B00-0BFF` | 0 | 0 | 1 | release | release | no wait |
| `0C00-0CFF` | 0 | 1 | 0 | sink | sink | always wait |
| `0D00-0DFF` | 0 | 1 | 0 | sink | sink | always wait |
| `0E00-0EFF` | 0 | 1 | 1 | sink | sink | always wait |
| `0F00-0FFF` | 0 | 1 | 1 | sink | sink | always wait |
| `1000-10FF` | 1 | 0 | 0 | release | sink | CAS-gated |
| `1100-11FF` | 1 | 0 | 0 | release | sink | CAS-gated |
| `1200-12FF` | 1 | 0 | 1 | release | release | no wait |
| `1300-13FF` | 1 | 0 | 1 | release | release | no wait |
| `1400-14FF` | 1 | 1 | 0 | sink | sink | always wait |
| `1500-15FF` | 1 | 1 | 0 | sink | sink | always wait |
| `1600-16FF` | 1 | 1 | 1 | sink | sink | always wait |
| `1700-17FF` | 1 | 1 | 1 | sink | sink | always wait |
| `1800-18FF` | 1 | 0 | 0 | release | sink | CAS-gated |
| `1900-19FF` | 1 | 0 | 0 | release | sink | CAS-gated |
| `1A00-1AFF` | 1 | 0 | 1 | release | release | no wait |
| `1B00-1BFF` | 1 | 0 | 1 | release | release | no wait |
| `1C00-1CFF` | 1 | 1 | 0 | sink | sink | always wait |
| `1D00-1DFF` | 1 | 1 | 0 | sink | sink | always wait |
| `1E00-1EFF` | 1 | 1 | 1 | sink | sink | always wait |
| `1F00-1FFF` | 1 | 1 | 1 | sink | sink | always wait |

Three classes exist, and only one depends on `CAS`:

- **no wait** - D2 releases `READY_D` regardless of `CAS`.
- **always wait** - every `A10=1` memory access; D2 sinks `READY_D`.
- **CAS-gated** - D2 sinks `READY_D` only while `cas_n=1`, so the access is
  held until the shared CAS rail goes active. In the D15 window this is
  exactly `1000-11FF`, `1800-19FF`.

The governing term is `A9=0 and cas_n=A12 and A15!=A12`, so the effect is
keyed to `A15` differing from `A12`, not to "the upper half" as such. The
D8 pager (`docs/d8-physical-decode.md`) also selects D15 at `C000-DFFF`,
where `A15=1` inverts which 4 KiB is CAS-gated, subject to D6's `ROM_SEL`
enable. Describing the effect as an upper-half property is an artifact of
looking only at the `0000-1FFF` image.

`READY_D` is the D input of D30 section A (`tm2_dff`, clocked by `phi2ttl`,
force-initialised from the D38 status strobe), so this table gives D2's
per-address contribution, not a cycle count. Per
`docs/d2-physical-truth.md` the exact per-cycle WAIT duration remains an
open clock/control boundary.

## Where the probed addresses fall

`T31-PHYSICAL.md` reports these RAM-resident probes on CS00015; the byte
column is cross-checked here against the burned
`spinoffs/jukuravi/firmware/diag-d0-low4k.bin`.

| Address | Byte in image | Recorded read | Wait class |
| --- | ---: | ---: | --- |
| `0017h` | `01` | `01` | no wait |
| `100Ch` | `B1` | `B1` | CAS-gated |
| `1017h` | `FE` | `FE` | CAS-gated |
| `106Fh` | `C3` | `C3` | CAS-gated |
| `1070h` | `0C` | `0C` | CAS-gated |
| `1071h` | `0A` | `0A` | CAS-gated |

All five upper probes sit in `1000-10FF`, i.e. entirely inside the single
CAS-gated class, and the one lower probe sits in a no-wait page. The
experiment therefore never compared the upper half against the lower half;
it compared **the CAS-gated class against an unwaited class**.

T31's own loader entry `0A0Ch` is in a no-wait page, and the lower half
also contains always-wait pages (`0400-07FF`, `0C00-0FFF`) that T31
demonstrably executes on CS00015. Both the no-wait and always-wait
mechanisms are therefore proven healthy on this board; the CAS-gated class
is the only one whose execution is untested except by the failing probe.

## Why no board mechanism can be fetch-selective

The premise under test is "correct upper-D15 data reads but a failing
upper-D15 instruction fetch". For that to be a board property, something
must distinguish the two cycles. Nothing does:

- In the 8080 status word, `MEMR` is asserted for both an M1 opcode fetch
  and a memory data read. `hdl/devices.v`'s 8238 decodes only `INP`, `OUT`
  and `INTA`, deriving `memr_n = ~(dbin & ~INP & ~INTA)` - identical for
  both cycle types.
- No `M1`-derived net exists in `kicad/juku.board.json` or the HDL, so no
  chip select, decode or wait input can see it.
- D2 itself takes no cycle-type input. For every `A10=0` address - which
  includes all six probes - `IORC_N` and `A14` are don't-cares, `WREQ_N` is
  a region select rather than a cycle qualifier, and the only remaining
  variable is the free-running `CAS`.
- D8/D6 ROM selection is address-only (`docs/d8-physical-decode.md`).

A `JMP 106Fh` fetches `C3` as an M1 cycle and `0C 0A` as ordinary read
cycles, so only the first byte is even nominally a different cycle type -
and that difference is invisible to this hardware.

## Access-time budget

`docs/hardware-map.md` gives a КР580ВМ80А CPU and `docs/fdc-readiness.md`
derives its tick arithmetic at 2 MHz, so a T-state is ~500 ns. An unwaited
8080 memory read is three T-states with data sampled in T3, leaving on the
order of two T-states (~1000 ns) from address-valid to data-required, less
address-buffer, D6/D8 select and data-buffer delays.

D15 is a 2764/27C64-class device (`docs/eprom-programming-images.md`),
whose common variants specify 250-450 ns access. Even the slowest fits the
unwaited budget with margin, and the conclusion is not sensitive to the
exact clock: at 2.5 MHz the budget is still ~800 ns. These are datasheet-
class figures and a first-order budget, not measurements.

Decisively, the CAS-gated class can only **lengthen** a cycle relative to
the no-wait class. Since the no-wait pages execute correctly on CS00015, a
uniform access-time shortfall cannot explain a failure confined to pages
that receive at least as much time.

## Does the factory firmware execute in the CAS-gated pages?

If the CAS-gated pages were never meant to hold code, our ROM layout would
be the faulty assumption rather than the board. Scanning `roms/ekta37.bin`
for absolute transfer instructions whose target lands in a CAS-gated page:

- distinct CAS-gated targets: 36
- of those, reached from more than one site: 5

| Target | Class | Sites |
| --- | --- | --- |
| `1062h` | CAS-gated | `1014`, `101C`, `1072` |
| `1076h` | CAS-gated | `0A6E`, `0B3B`, `0B9C` |
| `10AEh` | CAS-gated | `1099`, `10A8` |
| `1110h` | CAS-gated | `1101`, `110B` |
| `11E6h` | CAS-gated | `0308`, `0312` |

This is a byte-pattern scan, not a disassembly, so isolated hits may be
data. A target entered from several distinct sites is much harder to
explain as coincidence, and such targets exist. The factory firmware
appears to call into the CAS-gated pages, so executing code there is
within the machine's intended envelope and the T31 trampoline placement is
not by itself an invalid assumption.

## What this refutes and what survives

Refuted:

- **A uniformly slow substitute EPROM.** The failing pages get at least as
  much access time as the working ones.
- **"Code must not live in those pages."** The factory firmware targets
  them from multiple sites.
- **A fetch-selective board fault.** No decode, select or wait input on
  this machine can distinguish an M1 fetch from a memory read.

Still open:

- The real asymmetry is **CAS-gated versus unwaited**, not fetch versus
  read, and not upper versus lower. A fault in the CAS-gated release path
  fits every observation.
- `CAS` originates at D36.11 through R57, and its own input `D36_CAS_IN`
  (D36.12/.13) is an explicit unresolved continuity boundary -
  `docs/memory-timing-boundary.md` is headed "CAS SOURCE BOUNDARY
  PENDING". The same rail carries a video-cycle branch. CS00015's one
  confirmed fault (D55, per `docs/cs00015-service-record.md`) sits in the
  adjacent D54/D55/D56 video-timing cluster. A shared root cause is
  plausible but **not established**, and cannot be until the CAS source is
  closed.
- The five D2 address inputs (`A10`, `A14`, `A12`, `A15`, `A9` on pins
  1/3/5/6/7) are assigned by "scan + July-2026 D2/D4 solder local fits",
  not by traced continuity. The page geometry of the table above therefore
  inherits that reconstruction risk. The measured asymmetry on CS00015 does
  not - it is an observation, whatever the pin order turns out to be.
- `docs/cs00015-service-record.md` records three bytes of the machine's
  originally fitted D15 differing from the official image, with the offsets
  explicitly not retained. Those offsets should be captured; if any fall in
  a CAS-gated page it would sharpen this picture.

## Cheapest next discriminators

1. **Upper-half unwaited trampoline.** Burn a `JMP` into a page that is
    upper-half but *not* CAS-gated - `1200-13FF`, `1A00-1BFF` -
    and execute it the same way as `rom-exec-106f.bin`. Success there
    with continued failure at `106Fh` isolates the CAS-gated release path
    and clears A12 itself. Failure there too moves the fault onto A12
    delivery or the D15 socket's upper addressing, independent of waits.
2. **Always-wait upper trampoline** in `1400-17FF` separates "any wait in
    the upper half" from "specifically the CAS-gated wait".
3. **Re-run `rom-exec-106f.bin` after substituting D55**, which is already
    the recommended action for the known D55 fault. If the CAS video-cycle
    branch is involved, this may clear both symptoms at once.
4. **Cross-swap the burned EPROM into the donor board** and run the same
    probe, to separate our device and image from CS00015 entirely.

Probes 1 and 2 need no board rework and no new instrumentation, but they
do need one re-burned D15, because the currently burned image has no
reusable entry point in the classes under test.

### Trampoline availability in the burned image

A probe re-enters the resident loader by executing a `JMP 0A0Ch`
(`C3 0C 0A`) at the address under test. In
`spinoffs/jukuravi/firmware/diag-d0-low4k.bin` that sequence occurs at:

| Offset | Half | Wait class |
| --- | --- | --- |
| `065Ch` | lower | always wait |
| `0A06h` | lower | no wait |
| `106Fh` | upper | CAS-gated |

The distinction that matters is class *and* half, since the lower half is
already known to execute.

- covered: lower always wait
- covered: lower no wait
- covered: upper CAS-gated
- **missing: upper no wait**
- **missing: upper always wait**

The two missing combinations are precisely what probes 1 and 2 need, which
is why they need the re-burn.

The `C000-DFFF` alias does not avoid it. With `A12=0` there it presents
low-4K contents, so each low offset also appears at `C000+offset`; but a
CAS-gated alias needs address bits 10 and 9 both clear, and the two low
candidates fail that (`065C` has A10=1, `0A06` has A9=1). Aliases reaching
a class their direct address does not: none. Whether D6's
`ROM_SEL` enables that window at all is mode-dependent and was not
established here, but for this image the point is moot.

One burn can cover everything: add a `JMP 0A0Ch` at `1200h` (unwaited
upper) and at `1400h` (always-wait upper), keeping the existing `106Fh`
(CAS-gated). Three RAM trampolines then discriminate all three classes
against each other in a single bench session, with `rom-reenter-4000.bin`
as the no-upper-fetch control.
