# VJUGA rev B status

**ORDER HOLD.** The current candidate is a complete five-board machine: CPU,
Memory, expanded I/O, Backplane and Video. The
[five-board order plan](rev-b-five-board-order-plan.md) controls its scope;
[the release record](rev-b-five-board-release-gate.json) binds its exact sources,
archives and qualification evidence. Owner upload authorization is absent.

## Implemented and desk-qualified

| Area | Current implementation | Evidence |
| --- | --- | --- |
| CPU and bus | Z80 at 2.000 MHz, RC2014-compatible base bus plus extension, five slots | [Bus contract](rev-b-bus-contract.md) and card/boot gates |
| Memory | ROM/SRAM with reproducible ATF22V10 decode | GAL rebuild, Memory LVS and routed-board checks |
| I/O | 8251, populated 8255/8259, D57-compatible PIT, independent POST latch, ATF22V10 decode | [I/O expansion](rev-b-io-expansion.md), pin/LVS checks and fault controls |
| Serial | PIT-normal 19,200 baud; direct-clock 19,200/9,600 recovery; protected USB-TTL boundary | Serial electrical/console and integrated NETC10 gates |
| Video | Four-layer VGA card, local framebuffer and 25.175 MHz clock; three reproducible GAL designs | Video pin/LVS, timing, routed-plane and exact-part checks |
| Firmware | Reproducible EKTA3.7, NETC10 and DIAG 27C256 images; PIT initialization retained and early POST independent of RAM stack | ROM-set and integrated three-ROM gates |
| Physical design | Five routed sources, parts/power/mechanical checks and independently reviewed archives | [Pre-upload review](rev-b-five-board-preupload-review.md) and release record |

These are desk results. The bus, assembled boards, serial electrical behavior and
complete machine still require staged physical qualification. The first order
contains no FDC card; original raster generation and D57 channel-2 timing are
replaced by the autonomous VGA subsystem.

## Verification

From the repository root:

```sh
spinoffs/minimal-vga/sim/revb_tier_suite.sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py --self-test
```

The full suite includes behavioral, GAL, CAD and release checks. Inspect any
reported tool skips: a successful exit with skipped CAD checks does not prove
manufacturing readiness. `revb_tier_suite.sh --ci` is a behavioral smoke subset.
See the [execution guide](rev-b-execution-guide.md) for focused commands.

## Remaining boundaries

1. R5.R1: owner review of the exact five-archive candidate and explicit upload
   authorization. Technical PASS leaves **ORDER HOLD** in force.
2. R5.O1: vendor preview/DFM review and a separate owner order instruction,
   recorded in the [order record](rev-b-five-board-order-record.md).
3. R5.B1: receipt, programmed-device readbacks and staged assembly/power-up,
   recorded in the [bench template](rev-b-b1-bench-log.md).

The order and bench documents are prepared procedures, not completed physical
records. Earlier four-board packages and pre-expansion I/O layouts are historical
and must not be uploaded as the current candidate.
