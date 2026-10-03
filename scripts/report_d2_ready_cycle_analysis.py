#!/usr/bin/env python3
"""Derive D2 READY wait classes per ROM page and test the A12 fetch/read premise.

Desk analysis behind the CS00015 "A12 problem": reduce the validated D2 `.037`
table to a wait class for every page of the D15 window, locate the six probed
addresses in it, and check whether any board mechanism could make an
instruction fetch behave differently from a data read at the same address.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "ref/physical-proms/validated/d2_037.raw.bin"
FACTORY = ROOT / "roms/ekta37.bin"
PROBE_IMAGE = ROOT / "spinoffs/jukuravi/firmware/diag-d0-low4k.bin"
REPORT = ROOT / "docs/d2-ready-cycle-analysis.md"
EXPECTED_SHA256 = "953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b"

# T31-PHYSICAL.md records these RAM-resident probe results on CS00015.
PROBES = ((0x0017, 0x01), (0x100C, 0xB1), (0x1017, 0xFE),
          (0x106F, 0xC3), (0x1070, 0x0C), (0x1071, 0x0A))

# Absolute transfer opcodes, for the factory-firmware target scan.
TRANSFERS = {0xC3: "JMP", 0xCD: "CALL", 0xC2: "JNZ", 0xCA: "JZ", 0xD2: "JNC",
             0xDA: "JC", 0xE2: "JPO", 0xEA: "JPE", 0xF2: "JP", 0xFA: "JM",
             0xC4: "CNZ", 0xCC: "CZ", 0xD4: "CNC", 0xDC: "CC", 0xE4: "CPO",
             0xEC: "CPE", 0xF4: "CP", 0xFC: "CM"}


def prom_index(addr: int, cas_n: int, iorc_n: int = 1, wreq_n: int = 1) -> int:
    """Physical D2 address byte: {WREQ_N,A10,IORC_N,A14,CAS,A9,A15,A12}."""
    bit = lambda n: (addr >> n) & 1
    return ((wreq_n << 7) | (bit(10) << 6) | (iorc_n << 5) | (bit(14) << 4)
            | (cas_n << 3) | (bit(9) << 2) | (bit(15) << 1) | bit(12))


def released(raw: bytes, addr: int, cas_n: int) -> bool:
    """True when D2 releases READY_D (no wait contribution)."""
    return (raw[prom_index(addr, cas_n)] & 0xF) != 0


def wait_class(raw: bytes, addr: int) -> str:
    low, high = released(raw, addr, 0), released(raw, addr, 1)
    if low and high:
        return "no wait"
    if not low and not high:
        return "always wait"
    return "CAS-gated"


def main() -> int:
    raw = RAW.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"D2 raw image SHA256 changed: {sha}")
    if sorted(set(raw[i] & 0xF for i in range(256))) != [0x0, 0xF]:
        raise SystemExit("D2 low nibble is no longer strictly 0/F")

    pages = [(page << 8, wait_class(raw, page << 8)) for page in range(0x20)]

    def merge(bases: list[int]) -> str:
        """Collapse contiguous 256-byte pages into readable ranges."""
        spans: list[list[int]] = []
        for base in bases:
            if spans and base == spans[-1][1] + 0x100:
                spans[-1][1] = base
            else:
                spans.append([base, base])
        return ", ".join(f"`{lo:04X}-{hi + 0xFF:04X}`" for lo, hi in spans)

    gated = [base for base, cls in pages if cls == "CAS-gated"]
    factory = FACTORY.read_bytes()
    probe_image = PROBE_IMAGE.read_bytes()

    # Byte-pattern scan: data bytes alias as opcodes, so counts are indicative,
    # but a target reached from several distinct sites is unlikely to be noise.
    sites: dict[int, list[int]] = {}
    for i in range(len(factory) - 2):
        if factory[i] in TRANSFERS:
            target = factory[i + 1] | (factory[i + 2] << 8)
            if target < 0x2000 and wait_class(raw, target) == "CAS-gated":
                sites.setdefault(target, []).append(i)
    repeated = sorted((t, s) for t, s in sites.items() if len(s) > 1)

    out: list[str] = []
    add = out.append
    add("# D2 READY wait classes and the A12 fetch/read premise")
    add("")
    add("Status: **DESK ANALYSIS / FETCH-SELECTIVE PREMISE NOT SUPPORTED /")
    add("CAS-GATED CONFINEMENT REFUTED BY T32**")
    add("")
    add("The completed [T32](../spinoffs/jukuravi/T32-PHYSICAL.md) and")
    add("[T33](../spinoffs/jukuravi/T33-PLAN.md) evidence shows failure across all")
    add("three wait classes and identifies the fitted D1 increment-path fault.")
    add("The derivation below remains a model analysis, not a new measurement.")
    add("")
    add("This generated report re-derives, from the validated D2 `.037` READY PROM,")
    add("what wait treatment each page of the D15 window receives, and then asks")
    add("whether the CS00015 \"A12 problem\" as framed in")
    add("[`../spinoffs/jukuravi/T31-PHYSICAL.md`](../spinoffs/jukuravi/T31-PHYSICAL.md)")
    add("is represented by the modeled input classes. It only draws out what")
    add("the already-preserved tables imply.")
    add("")
    add("Regenerate with `python3 scripts/report_d2_ready_cycle_analysis.py`.")
    add("The generator verifies the D2 hash and derives page classes. Probe bytes")
    add("are compared with the diagnostic image; factory transfers are byte-pattern")
    add("matches. Board/HDL descriptions below are transcriptions, not fresh net checks.")
    add("")
    add("## Provenance")
    add("")
    add(f"- Raw D2 image: `ref/physical-proms/validated/d2_037.raw.bin`, SHA256 `{sha}`")
    add("- Input order (from `docs/d2-reconstruction-constraints.md`):")
    add("  `{WREQ_N, A10, IORC_N, A14, CAS, A9, A15, A12}`")
    add("- Raw `0` sinks `READY_D`; raw `F` releases it to the R6 pull-up.")
    add("- Memory-cycle assumption: `WREQ_N=1` (D6.11 `RAM_SEL` inactive, so not a")
    add("  DRAM access) and `IORC_N=1` (not an I/O read). `hdl/juku_top.v` wires the")
    add("  PROM as `{wreq_n, A[10], iorc_n, A[14], cas_n, A[9], A[15], A[12]}`, so the")
    add("  table's `CAS` bit is the active-low `cas_n` rail.")
    add("")
    add("Naming note: `docs/d2-physical-truth.md` calls pin 2 `XACK_N` while")
    add("`docs/d2-reconstruction-constraints.md` and the HDL call it `IORC_N`. The")
    add("constraints file proves these are the same conductor (`-XACK` and `-IORC`")
    add("labels at the identical factory edge coordinate 106C), so this is an alias,")
    add("not a conflict.")
    add("")
    add("## Wait class per page of the D15 window")
    add("")
    add("| Page | A12 | A10 | A9 | `cas_n=0` | `cas_n=1` | Class |")
    add("| --- | ---: | ---: | ---: | --- | --- | --- |")
    for base, cls in pages:
        bit = lambda n: (base >> n) & 1
        lo = "release" if released(raw, base, 0) else "sink"
        hi = "release" if released(raw, base, 1) else "sink"
        add(f"| `{base:04X}-{base + 0xFF:04X}` | {bit(12)} | {bit(10)} | "
            f"{bit(9)} | {lo} | {hi} | {cls} |")
    add("")
    add("Three classes exist, and only one depends on `CAS`:")
    add("")
    add("- **no wait** - D2 releases `READY_D` regardless of `CAS`.")
    add("- **always wait** - every `A10=1` memory access; D2 sinks `READY_D`.")
    add("- **CAS-gated** - D2 sinks `READY_D` only while `cas_n=1`, so the access is")
    add("  held until the shared CAS rail goes active. In the D15 window this is")
    add("  exactly " + merge(gated) + ".")
    add("")
    add("The governing term is `A9=0 and cas_n=A12 and A15!=A12`, so the effect is")
    add("keyed to `A15` differing from `A12`, not to \"the upper half\" as such. The")
    add("D8 pager (`docs/d8-physical-decode.md`) also selects D15 at `C000-DFFF`,")
    add("where `A15=1` inverts which 4 KiB is CAS-gated, subject to D6's `ROM_SEL`")
    add("enable. Describing the effect as an upper-half property is an artifact of")
    add("looking only at the `0000-1FFF` image.")
    add("")
    add("`READY_D` is the D input of D30 section A (`tm2_dff`, clocked by `phi2ttl`,")
    add("force-initialised from the D38 status strobe), so this table gives D2's")
    add("per-address contribution, not a cycle count. Per")
    add("`docs/d2-physical-truth.md` the exact per-cycle WAIT duration remains an")
    add("open clock/control boundary.")
    add("")
    add("## Where the probed addresses fall")
    add("")
    add("`T31-PHYSICAL.md` reports these RAM-resident probes on CS00015; the byte")
    add("column is cross-checked here against the burned")
    add("`spinoffs/jukuravi/firmware/diag-d0-low4k.bin`.")
    add("")
    add("| Address | Byte in image | Recorded read | Wait class |")
    add("| --- | ---: | ---: | --- |")
    for addr, recorded in PROBES:
        got = probe_image[addr]
        mark = f"`{got:02X}`" if got == recorded else f"`{got:02X}` MISMATCH"
        add(f"| `{addr:04X}h` | {mark} | `{recorded:02X}` | {wait_class(raw, addr)} |")
    add("")
    add("All five upper probes sit in `1000-10FF`, i.e. entirely inside the single")
    add("CAS-gated class, and the one lower probe sits in a no-wait page. The")
    add("experiment therefore never compared the upper half against the lower half;")
    add("it compared **the CAS-gated class against an unwaited class**.")
    add("")
    add("T31's own loader entry `0A0Ch` is in a no-wait page, and the lower half")
    add("also contains always-wait pages (`0400-07FF`, `0C00-0FFF`) that T31")
    add("demonstrably executes on CS00015. At the end of T31, the CAS-gated class")
    add("was therefore the only upper-half class tested. T32 subsequently tested")
    add("all three upper-half wait classes and found the same failure in each,")
    add("refuting wait-class confinement as stated in the supersession note.")
    add("")
    add("## Modeled fetch/read inputs")
    add("")
    add("The premise under test is \"correct upper-D15 data reads but a failing")
    add("upper-D15 instruction fetch\". The modeled decode paths have no explicit")
    add("opcode-fetch qualifier:")
    add("")
    add("- In the 8080 status word, `MEMR` is asserted for both an M1 opcode fetch")
    add("  and a memory data read. `hdl/devices.v`'s 8238 decodes only `INP`, `OUT`")
    add("  and `INTA`, deriving `memr_n = ~(dbin & ~INP & ~INTA)` - identical for")
    add("  both cycle types.")
    add("- The recorded board model supplies no `M1` qualifier to the ROM-select")
    add("  or D2 wait inputs.")
    add("- D2 itself takes no cycle-type input. For every `A10=0` address - which")
    add("  includes all six probes - `IORC_N` and `A14` are don't-cares, `WREQ_N` is")
    add("  a region select rather than a cycle qualifier, and the only remaining")
    add("  variable is the free-running `CAS`.")
    add("- D8/D6 ROM selection is address-only (`docs/d8-physical-decode.md`).")
    add("")
    add("A `JMP 106Fh` fetches `C3` as an M1 cycle and `0C 0A` as ordinary read")
    add("cycles, so only the first byte is even nominally a different cycle type -")
    add("The listed decode inputs do not select on that distinction. This does not")
    add("rule out physical differences in edge timing, loading, or CPU behavior.")
    add("")
    add("## Does the factory firmware execute in the CAS-gated pages?")
    add("")
    add("If the CAS-gated pages were never meant to hold code, our ROM layout would")
    add("be the faulty assumption rather than the board. Scanning `roms/ekta37.bin`")
    add("for absolute transfer instructions whose target lands in a CAS-gated page:")
    add("")
    add(f"- distinct CAS-gated targets: {len(sites)}")
    add(f"- of those, reached from more than one site: {len(repeated)}")
    add("")
    if repeated:
        add("| Target | Class | Sites |")
        add("| --- | --- | --- |")
        for target, site_list in repeated:
            joined = ", ".join(f"`{s:04X}`" for s in sorted(site_list))
            add(f"| `{target:04X}h` | {wait_class(raw, target)} | {joined} |")
        add("")
    add("This byte-pattern scan is not a disassembly or execution trace. Repeated")
    add("matches remain candidate transfers; data bytes can produce the same patterns.")
    add("It does not prove that these sites execute or establish an EPROM timing margin.")
    add("")
    add("## Current disposition")
    add("")
    add("T32/T33 measured the same A12-low second-byte failure across CAS-gated,")
    add("no-wait, and always-wait classes. The fitted D1 increment-path diagnosis")
    add("and replacement confirmation are owned by the linked physical records.")
    add("This table analysis does not repeat those measurements or qualify hardware.")
    add("")
    add("D2's input mapping is recorded in [D2 constraints](d2-reconstruction-constraints.md).")
    add("The unresolved CAS source and physical WAIT duration remain generic timing")
    add("boundaries in [memory timing](memory-timing-boundary.md); they do not keep")
    add("the completed CS00015 diagnosis open.")
    add("")

    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}: {len(pages)} pages classified, "
          f"{len(gated)} CAS-gated, {len(sites)} factory targets in gated pages "
          f"({len(repeated)} multi-site).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
