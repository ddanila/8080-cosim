# VJUGA rev B — R5.J3 independent pre-upload review

Status: **PASS / ORDER HOLD** on 2026-08-28. Reviewer: **Codex**.
Review signature: `Codex / 2026-08-28 / package source 90012621`.

This review covers the five independent bare-PCB release archives only. It does
not authorize upload, add an item to a vendor cart, or place an order. The owner
must still perform R5.R1 and explicitly change `ORDER HOLD` before any upload.

## Independently rendered package review

`kicad/revb/review_revb_release.py --self-test` reads the ZIP contents rather
than the export directories and renders them with gerbv 2.10.0-2build1. The
reviewed candidate uses source revision
`90012621b45a923e8315c0e5ca6a38092b518885` and JLC profile SHA-256
`71389d73858ecb5950a5eb2066258915e2b87e4176dba02c59e6ebf1302f036a`.
The typography/content findings and immutable font identity are recorded in
`rev-b-silkscreen-audit.md`.

| Design | Separate Gerber/drill renders | Top/bottom composites | Result |
|---|---:|---:|---|
| CPU | 8 | 2 | PASS |
| Memory | 8 | 2 | PASS |
| I/O | 8 | 2 | PASS |
| Backplane | 8 | 2 | PASS |
| Video | 10 | 2 | PASS |
| **Total** | **42** | **10** | **PASS** |

Visual checklist:

- [x] Every copper, mask, silk, outline and Excellon member renders separately.
- [x] Each board has one closed rectangular outline at its intended aspect ratio.
- [x] Top/bottom copper, mask apertures and drill hits share one origin and align.
- [x] Connector rows, IC land patterns, polarised footprints and mounting holes
      appear in the intended locations; no layer is visibly translated or clipped.
- [x] Video In1 is a continuous GND plane and In2 a continuous VCC plane, with
      the expected antipads and without an unintended split/island.
- [x] Every visible silk text item uses the pinned `GOST CAD KK` Book face from
      the recorded font file; title, ordinary-label and safety-label sizing is
      consistent across all five boards.
- [x] Top legends are legible and retain revision, assembly references, DNP,
      slot, orientation, voltage and no-hot-plug markings.
- [x] All five bottom legends render nonblank. CPU, Memory, I/O and Video carry
      mirrored pin-1 cues; Backplane carries the underside `U_RST` service cue.
- [x] Mirrored bottom composites have the expected fabrication-view orientation.
- [x] No unresolved visual finding remains.

The independent gate also rejects a wrong footprint count, a changed programmed
artifact hash, and a programmed device moved into the DNP set.

## First-system BOM and programming reconciliation

The machine-readable contract is `kicad/revb/five-board-bom.json`. Its references
are independently compared with the five routed PCB sources and their five
connectivity descriptions.

| Design | PCB footprints | First-system populated | DNP |
|---|---:|---:|---:|
| CPU | 7 | 7 | 0 |
| Memory | 10 | 10 | 0 |
| I/O | 19 | 12 | 7 |
| Backplane | 41 | 41 | 0 |
| Video | 54 | 54 | 0 |
| **Total** | **131** | **124** | **7** |

The seven DNP footprints are I/O `U4`, `U5`, `U6`, `C4`, `C5`, `C6` and
`J_KBD`, reserved for B3. The first system needs **six programmed devices**:
Memory `U1` 27C256, Memory `U3` and I/O `U2` GALs, and Video `U5`/`U6`/`U7`
GALs. All six artifact sizes and SHA-256 values match the contract. Thus the
five reproducible JEDECs are necessary but not sufficient: the physical
27C256 image is the sixth programmed artifact.

## Dated JLCPCB pre-upload quote

Captured at `2026-08-28T07:40:54+03:00` with Google Chrome 151 from the
[official JLCPCB instant quote](https://cart.jlcpcb.com/quote/), without a file
upload, cart mutation or login. Each row is five copies of one independent
single-PCB design: FR-4 TG135, 1.6 mm, green mask, white silk, lead-free HASL,
1 oz outer copper, flying-probe test, regular ±0.2 mm outline tolerance, no
vendor mark, and production-file confirmation **Yes**. The four-layer quote
uses its 0.5 oz inner copper and no controlled impedance.

This same-day quote snapshot is retained after the silk-only correction because
board dimensions, layer counts and every fabrication selection are unchanged;
the corrected archives and renders were regenerated and reviewed independently.

| Design | Size | Layers | Via covering | Qty | Web fabrication | Standard build |
|---|---:|---:|---|---:|---:|---:|
| CPU | 100×70 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Memory | 100×60 mm | 2 | Tented | 5 | $6.24 | 2 days |
| I/O | 100×100 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Backplane | 100×100 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Video | 100×100 mm | 4 | Plugged | 5 | $13.24 | 3–4 days |
| **Pre-upload fabrication subtotal** |  |  |  | **25 PCBs** | **$38.50** | **3–4 days critical path** |

The form displayed no configuration warning for these selections. It allows
Tented vias for the two-layer rows but disables that button for the standard
four-layer row and selects Plugged; the frozen profile now encodes that split.
Production-file confirmation contributes $1.04 per design and is included above.

The $38.50 subtotal is a dated web estimate, not a payable total. It excludes
combined shipping, tax, coupons and exchange-rate movement. The page showed a
standalone DHL estimate of $28.67 for each separately evaluated row; those
standalone estimates must not be added together or treated as the combined-cart
shipping quote. Actual detected dimensions/layers, DFM warnings, combined
shipping and the payable total remain R5.O1 upload/checkout evidence after owner
release. The official ordering instructions likewise make Gerber upload the
point where dimensions and layers are automatically analysed.

## Exact reviewed archive identity

| Design | ZIP bytes | SHA-256 |
|---|---:|---|
| CPU | 26,975 | `2335e88fc54e5d6efa7f8ba48d1bcb814b9d7e9960d581d4506c95aae361389d` |
| Memory | 33,740 | `a2c903d130d87b9ea970fe8d9c0408d3751c181eb51a3406a712042874bff7b2` |
| I/O | 48,709 | `fb29708fab4d1070101ca26f0a053b4d059fbb8956847bb6382f97478417bc19` |
| Backplane | 64,047 | `1a642c0b7d5ed282da03ee263d7a66ee00d6ee93394e456dc4799f501a5ea590` |
| Video | 437,926 | `46e13e63c3b4df4eb05f70c38dd2d810860d6503b36db85feabcace324b5f4ab` |

R5.J3 is therefore complete. The next gate is R5.R1: present this evidence to
the owner and retain `ORDER HOLD` unless the owner explicitly releases these
exact hashes for upload. The hash-bound state and authorization schema are frozen
in `rev-b-five-board-release-gate.json` and enforced by
`kicad/revb/check_revb_release_gate.py`.
