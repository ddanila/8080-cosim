# VJUGA rev B — five-board upload, DFM, and order record (R5.O1)

Status: **TEMPLATE READY / ORDER HOLD**. Do not upload while
`rev-b-five-board-release-gate.json` says `ORDER HOLD`. This record covers five
independent bare-PCB designs only: CPU, Memory, I/O, Backplane, and Video. It is
not a panel or a PCBA order.

## Three controlled gates

1. **Upload gate.** Immediately before opening the vendor upload form, run:

   ```sh
   spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
     --require-released --package-root fab/minimal-vga/revb/package
   ```

   Stop unless it passes. Owner release authorizes upload of only the exact five
   hashes below for production-file preview. It does not authorize accepting a
   vendor edit or paying for the order.
2. **Order/payment gate.** After all five pre-payment Gerber Viewer previews,
   warnings, options, quantities, combined shipping/tax, and final payable total are
   recorded, present those sections to the owner. Submit the order or payment only
   after a new, explicit instruction to do so; record that instruction, owner, and
   timestamp. Select **Confirm Production File** for every design.
3. **Production gate.** JLCPCB generates the production files after payment. When
   notified, download each production archive from Order History and compare its
   `ok` Gerbers with both the `yg` originals and the independently reviewed release
   render. Do not click **Yes, please proceed to production** before this comparison.
   If it changes design intent, choose **not good, modification needed**, record the
   discrepancy, and do not approve production until it has a reviewed disposition.

Any vendor-requested copper, drill, outline, layer, or archive change invalidates
the recorded hash. Reject the changed preview, return to R5.J2/J3/R1, generate and
review a new candidate, and obtain a new exact-hash release. Never silently accept
or edit production data in the vendor UI.

## Released candidate and session identity

| Field | Recorded value |
|---|---|
| Upload-gate command result | pending |
| Release-gate status / owner / timestamp | pending |
| Source revision | `6962a9a4ec6bfa67703112bbc828287d94ebc5b8` |
| Browser/session date | pending |
| Vendor | JLCPCB |
| Delivery unit | five separate PCB designs; no panelization |
| Assembly | bare PCB only; no PCBA |
| Production-file confirmation | **Yes**, required for all five designs |

## Per-design upload and preview

Upload each archive directly from `fab/minimal-vga/revb/package/`. Recompute its
SHA-256 before upload and enter the detected dimensions and layer count from the
vendor form; they must equal the expected values below. Store screenshots or PDFs
outside the repository if they contain account/address details, and record a safe
local evidence name here.

| Design | Expected size / layers | Exact released ZIP SHA-256 | Uploaded hash | Vendor detection | Preview evidence | Result |
|---|---|---|---|---|---|---|
| CPU | 100x70 mm / 2 | `b83ee98722bf3035059c192ac25406cf69e41931704c2f4493dca2f8f981e0a0` | pending | pending | pending | pending |
| Memory | 100x60 mm / 2 | `002ecd84ecfefde6b6ae8fc3b2859b8d4599294e5821dd443b451916e708831e` | pending | pending | pending | pending |
| I/O | 100x100 mm / 2 | `a86c1ac422bdfb5dbd4225fde0fc26016438b93e21161c7f6de1e3c487c1589a` | pending | pending | pending | pending |
| Backplane | 100x100 mm / 2 | `8ed116a001f1c575df0355800d52206de8297ae7a64e4c7661400cd625a4deca` | pending | pending | pending | pending |
| Video | 100x100 mm / 4 | `05180d8fa2084feec9bfdc4fa5aba89350dc681e643ac5a4e3f239ed69d17dc1` | pending | pending | pending | pending |

For every preview, inspect rather than infer:

- one closed outline at the expected scale; no unintended cutout or slot;
- correct top/bottom copper, mask, and silkscreen, with all plated drill hits;
- Video additionally has two inner copper layers, ordered as signal / GND / VCC5 /
  signal, with continuous GND and VCC5 planes;
- no paste, adhesive, courtyard, fab, user, assembly, or STEP layer;
- no missing silk polarity/orientation marks, mask shift, drill shift, clipped text,
  or vendor-added copper;
- the **Confirm Production File** option is enabled for later post-payment review.

## Exact fabrication selections

| Selection | CPU / Memory / I/O / Backplane | Video | Recorded vendor value |
|---|---|---|---|
| Quantity | 5 each | 5 | pending |
| Material / Tg | FR-4 TG135 | FR-4 TG135 | pending |
| Thickness | 1.6 mm | 1.6 mm | pending |
| Copper | 1 oz outer | 1 oz outer, 0.5 oz inner | pending |
| Stack-up | standard 2-layer | JLC7628 standard 4-layer | pending |
| Solder mask / silk | green / white | green / white | pending |
| Surface finish | lead-free HASL | lead-free HASL | pending |
| Via covering | Tented | Plugged | pending |
| Electrical test | flying probe | flying probe | pending |
| Outline tolerance | regular ±0.2 mm | regular ±0.2 mm | pending |
| Vendor mark | none | none | pending |
| Impedance control | no | no | pending |
| Production-file confirmation | yes | yes | pending |

## Warnings and DFM disposition

Create one row for every vendor warning, question, or proposed adjustment. An empty
vendor result must be written as `none shown`; it must not be left implicit.

| Design | Warning / requested change | Vendor evidence | Accept or reject | Technical disposition / new release required? | Reviewer |
|---|---|---|---|---|---|
| pending | pending | pending | pending | pending | pending |

All five design previews must be accepted by a named reviewer before the order gate.
If the vendor cannot fabricate an exact released archive under the frozen profile,
stop; do not substitute a board or order a partial set.

## Combined quote and order gate

| Field | Recorded value |
|---|---|
| PCB subtotal for all five designs | pending |
| Combined shipping | pending |
| Tax / duties collected | pending |
| Discounts / credits | pending |
| Final payable total and currency | pending |
| Longest quoted fabrication lead time | pending |
| Shipping method / delivery estimate | pending |
| Delivery address checked by owner | pending |
| Owner order instruction (verbatim) | pending |
| Owner identity / ISO timestamp | pending |
| Operator / reviewer | pending |

Only after the second gate is complete: submit payment, then record the vendor order
ID and immutable order-summary evidence. Do not store payment credentials or a full
postal address in this repository.

## Post-payment production-file confirmation

This is a real hold after payment, not a retrospective note. For each design, record
the downloaded production archive hash and separately inspect outline, drills, every
copper layer, mask, and silkscreen. Manufacturing-only naming/panel tooling may be
recorded as such; any changed finished-board geometry, connectivity, holes, mask, or
legend is a discrepancy requiring rejection and disposition.

| Design | Production archive SHA-256 | `yg` original matches upload | `ok` vs released design | Discrepancies / disposition | Confirmed by / ISO time |
|---|---|---|---|---|---|
| CPU | pending | pending | pending | pending | pending |
| Memory | pending | pending | pending | pending | pending |
| I/O | pending | pending | pending | pending | pending |
| Backplane | pending | pending | pending | pending | pending |
| Video | pending | pending | pending | pending | pending |

Only after the corresponding row passes may the operator tell JLCPCB to proceed to
production for that design. A vendor revision must be downloaded and reviewed again;
never approve it from an email description alone.

| Completion field | Recorded value |
|---|---|
| Vendor order ID | pending |
| Order placed ISO timestamp | pending |
| Final quantities | pending |
| Submitted archive hashes rechecked | pending |
| Production-file confirmations accepted | pending |
| Safe order-summary evidence name | pending |
| R5.O1 result | pending |

R5.O1 passes only when every pending field relevant to the actual order is replaced
with observed evidence, all five exact hashes were submitted unchanged, and the
order ID exists, and all five post-payment production files are confirmed. Delivery
then opens R5.B1 in `rev-b-b1-bench-log.md`.

Vendor-flow references checked 2026-08-28:

- [JLCPCB PCB ordering steps](https://jlcpcb.com/help/article/how-do-i-place-an-order)
- [JLCPCB production-file confirmation](https://jlcpcb.com/help/article/how-to-confirm-the-production-file)
- [JLCPCB ordering instructions and Gerber Viewer scope](https://jlcpcb.com/help/article/instructions-for-ordering)
