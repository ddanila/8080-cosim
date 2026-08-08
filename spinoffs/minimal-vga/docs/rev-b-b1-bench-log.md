# VJUGA rev B B1 — order and first-article bench record (T1.10/T1.11)

Fill this record as the four B1 bare-PCB ZIPs are uploaded and the first set is built.
Do not mark observations from expectation. Do not release duplicate population or the
B2 video PCB until every failed row has a disposition.

## T1.10 order record

| Field | Recorded value |
|---|---|
| Vendor / order ID | pending |
| Upload and preview date | pending |
| Board stack-up | 2 layer, FR-4, 1.6 mm; copper/finish pending vendor preview |
| Ordered quantities | pending (one assembled set; surplus bare boards held) |
| Vendor DFM warnings / accepted exceptions | pending |
| Approver | pending |

Upload only the four ZIPs below from `fab/minimal-vga/revb/package/`. Before payment,
compare them with `SHA256SUMS`, inspect every vendor layer preview, and record the hash
the vendor actually received.

| Board | Nominal size | Expected SHA-256 | Uploaded hash / preview result |
|---|---:|---|---|
| mem | 100 × 60 mm | `7653b88b822e7d7a763a34e36ea2ef3c3f3128103af793af3a5ad2d07cdcbfcf` | pending |
| io | 100 × 100 mm | `d731710de520421e933d3ff18f57423a47556c2497220da97b3063bf8b10860a` | pending |
| cpu | 100 × 70 mm | `f1cbb2e46375c4c2136526bfe36317c157a64a6380d31f3c9ef0a2e4d9ffc578` | pending |
| backplane | 100 × 120 mm | `85721dc7371150abff9d398861f870b47ef315d1210705387b216130b65bad94` | pending |

Vendor-preview checklist:

- [ ] Dimensions and two copper layers match the table; no vendor auto-scaling.
- [ ] Board outline is one closed rectangle; no cutouts were inferred from drawings.
- [ ] Top/bottom copper, mask and silk are assigned to the correct sides.
- [ ] Plated drill hits appear at every DIP/header/socket pad and via.
- [ ] Backplane USB4085 area retains 0.15 mm minimum clearance; no DFM edit accepted silently.
- [ ] No paste, adhesive, courtyard, fab, user or assembly layer was uploaded.
- [ ] Surface finish, copper weight, solder-mask color and shipping choice are recorded.

## Build identity

| Item | Recorded value |
|---|---|
| Board markings / lot codes | pending |
| `revb_bringup.bin` SHA-256 | `edfdabda362cefd6716acd2fe70b8befa500cb5983afe097ccd2d4a0e8447892` |
| Programmed ROM device / readback SHA-256 | pending |
| Memory GAL device / source / fuse checksum | pending |
| I/O GAL device / source / fuse checksum | pending |
| CPU oscillator fitted / measured | pending |
| UART oscillator fitted / measured baud | pending |
| Exact populated ICs and date codes | pending |
| DNP parts confirmed absent (I/O U4/U5/U6 and B3-only paths) | pending |

## T1.11 staged bring-up

Use a current-limited bench supply at `J_PWR` first: pin 1=`VCC5`, pin 2=`GND`.
`J_PWR` bypasses the USB polyfuse, so keep the current limit conservative and never
connect USB-C and the bench supply simultaneously. Power down before inserting/removing
a card; keying is convention-only.

| Step | Expected result | Observed result / evidence | Pass |
|---|---|---|:---:|
| 1. Bare-board inspection | Correct outline, drill registration, readable pin-1/orientation silk; no shorts/opens visible | pending | ⬜ |
| 2. Bare mechanical fit | Each card seats in at least slots 1–3 in the marked orientation; no forced insertion; measure adjacent-card gap | pending | ⬜ |
| 3. Backplane only, current limited | +5 V and GND correct at every slot; RESET_N asserts low and releases high; idle current recorded | pending | ⬜ |
| 4. CPU card, no memory/I/O | Clock reaches every slot; frequency and RESET_N timing recorded; no abnormal current/heat | pending | ⬜ |
| 5. NOP free-run | With the documented NOP plug, A0–A15 count and control/refresh activity is plausible at the analyzer header | pending | ⬜ |
| 6. Memory card | ROM/GAL readback hashes match; `J_OBS` shows ROM/RAM selects with no overlap; supply/current remain sane | pending | ⬜ |
| 7. I/O minimum population | 8251 + decode GAL + baud oscillator only; FTDI crossover checked before attaching host | pending | ⬜ |
| 8. Bring-up ROM | Serial stream is exactly `VJUGA rev B bring-up`, `RAM PASS`, `ROM OK`, `READY`; 47 bytes total | pending | ⬜ |
| 9. RAM boundary/retention | Test covers 0x4000–0xD6FF; 0xD700–0xD7FF remains reserved for stack/variables; repeated cold boots pass | pending | ⬜ |
| 10. Bus timing/current | Worst read/write margins and total current recorded against the ~712 mA budget | pending | ⬜ |
| 11. Keying/clearance disposition | Measured gap compared with 4.16 mm conservative model; reversed-insertion mitigation accepted or changed | pending | ⬜ |

## Exit decision

| Decision | Recorded value |
|---|---|
| All T1.11 rows pass | pending |
| Discrepancies and dispositions | pending |
| Duplicate B1 population released | no — pending first-article pass |
| B2 TI.5+ PCB work/tape-out released | no — pending first-article pass |
| Reviewer / date | pending |
