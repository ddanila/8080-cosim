# Processor X4 to НГМД wire map

Status: **REVIEWED CONNECTOR TRANSCRIPTION / SOURCE-MODEL CORRECTION REQUIRED**

This note reconciles the processor-module floppy connector on
`ДГШ5.109.009 Э3`, sheet 3, with the recovered НГМД block
`ДГШ3.065.008 Э3`. Two read passes were made over the native detail frames
and contrast-enhanced crops, with the overview frames used as an independent
layout check.

The drawings establish connector intent, not target-board copper continuity.
Owner continuity still outranks them where it exists. No separate external
cable assembly drawing is present in this batch, so `X4` to `XS5`
straight-through mating is identified by the exact contact-number and signal
agreement on every used signal, not by an unseen cable.

## Guarded primary frames

| Drawing region | Source frame | SHA256 |
| --- | --- | --- |
| processor sheet-3 overview | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` | `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047` |
| processor D93 host bus and control pins | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101637906.jpg` | `ba6f618ea610f05617cde668660a767c103116bcd55f46862a36cbe385ee26e4` |
| processor D100 outputs and X4.6-.22 | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` | `86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7` |
| processor D98 inputs and X4.7/.8/.14/.15/.23 | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101644861.jpg` | `8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67` |
| processor sheet-1 D26 Port-C continuations | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101809608.jpg` | `62ee9a1ce20ef418bbbb5e49ca8b79f2ff7d0fc317c9c9ffe1a087277067d004` |
| НГМД overview | `ref/photos/dgsh3-065-008-e3/PXL_20260718_121821197.jpg` | `d4f9604f3f35ea9bfa5f028f017e084e66390892f2e703feb579d27c668d1ff7` |
| НГМД drive/XS4-to-XS5 tables | `ref/photos/dgsh3-065-008-e3/PXL_20260718_121837340.jpg` | `aa1f3ed11c5b224d471c74bf2404b0019b9f08edc5fe54dc271daf069fce21e2` |
| НГМД second-drive table overlap | `ref/photos/dgsh3-065-008-e3/PXL_20260718_121849598.jpg` | `8addcb589b734db9b21a47593d144c17531c13e8c42a3b1e42d2899e5f037395` |

## Processor-module X4

The leading dash below is copied from the processor drawing. Rail `A` is the
sheet's +5 V rail. Contacts absent from sheet 3 are not assigned from analogy.

| X4 | Processor sheet-3 signal | Drawn local endpoint / disposition |
| ---: | --- | --- |
| 1 | NC | explicitly drawn as an unconnected contact |
| 2-5 | not shown on sheet 3 | older `.006` sheet-1 tape-control assignments are revision-stale and require separate disposition |
| 6 | GND | ground symbol at the contact |
| 7 | `-WR.PROTECT` | D98 input channel A3 |
| 8 | `-READY` | D98 input channel A4, then the D28.1 inverter section toward D93 READY |
| 9 | `-STEP` | D100 B3/pin 18 |
| 10 | `TG43` | D100 B1/pin 16 |
| 11 | `-WR.DATA` | D100 B4/pin 14 |
| 12 | +5 V (`A`) | joined to X4.13 |
| 13 | +5 V (`A`) | joined to X4.12 |
| 14 | `-TR.00` | D98 input channel A1 |
| 15 | `-INDEX` | D98 input channel A2 |
| 16 | `-DIR` | D100 B2/pin 19; the handwritten Latin-looking `TIR` label is the D93 `DIR` channel |
| 17 | `-H.LOAD` | D100 B6/pin 17 |
| 18 | `-WR.GATE` | D100 B5/pin 15 |
| 19 | `-MOTOR.ON` | D100 B7/pin 13 |
| 20 | `S.SEL` | D100 B8/pin 12 |
| 21 | `-D.SEL1` | D28 inverter output pin 2; R98 is the pull-up |
| 22 | `-D.SEL0` | D28 inverter output pin 4 |
| 23 | `RD.DATA` | D98 input channel A0 |

The D98 output side is also explicit: its B1/B2/B3 channels reach D93
TR00/INDEX/WPRT pins 34/35/36. The READY channel passes through the newly used
D28 pins 5/6 before D93.32. `RD.DATA` enters the read-separator path rather
than D93 RAW READ directly.

## Processor-side source map

The same drawing closes the host bus that the earlier photo reconstruction
had assigned to D100. Sheet 3 labels the eight conductors entering D93
DAL0-DAL7/pins 7-14 as the sheet-1 `D0`-`D7` bundle. They are direct system
data-bus connections; no transceiver lies between D0-D7 and D93.

Sheet 1 numbers the six D26 Port-C continuations beside pins 16,17,13,12,11,
and 10, and repeats those numbers beside their destination labels. The exact
floppy control assignment is therefore:

| D26 endpoint | Sheet-1 continuation | Sheet-3 endpoint / disposition |
| --- | ---: | --- |
| PC2 / pin 16 | 1 | `MOTOR EN` -> D100 A7/pin 7 |
| PC3 / pin 17 | 2 | `5\"/8\"`; target sheet-3 destination not shown |
| PC4 / pin 13 | 3 | `FM/MFM` -> D93 DDEN/pin 37 |
| PC5 / pin 12 | 4 | `D_SEL` -> D28 input pin 1 |
| PC6 / pin 11 | 5 | `S.SEL` -> D100 A8/pin 8 |
| PC7 / pin 10 | 6 | `POF`; sheet-2 destination |

D28 output pin 2 is drawn back into input pin 3, so pin 2 produces
`-D.SEL1` and the second inversion at pin 4 produces complementary
`-D.SEL0`. D100 input pins 4,1,2,5,3 receive D93 TG43, DIR, STEP, WG, and HLD
respectively; input pin 6 receives the write-data/precompensation path. D100
control pins 9 and 11 share the sheet-3 continuation marked `"1"`; the
upstream source of that continuation remains to be transcribed before it is
named semantically.

## НГМД external XS5

The НГМД drawing uses hierarchical drive assemblies `A2` and `A3`. Each has
its own power connector `X1`, 34-contact signal connector `X2`, and a
17-contact intermediate plug (`XS3` or `XS4`). Both intermediate plugs fan
out to the common external 23-contact `XS5`.

| XS5 | НГМД signal | Processor agreement |
| ---: | --- | --- |
| 1-6 | GND returns | X4.6 agrees; X4.1-.5 require cable/revision disposition |
| 7 | `W.PROT` | X4.7 `-WR.PROTECT` |
| 8 | `RDY` | X4.8 `-READY` |
| 9 | `STEP` | X4.9 `-STEP` |
| 10 | absent | processor-only X4.10 `TG43` |
| 11 | `W.DATA` | X4.11 `-WR.DATA` |
| 12-13 | absent | processor X4.12/.13 are +5 V and have no НГМД mate in this table |
| 14 | `TR.0` | X4.14 `-TR.00` |
| 15 | `INDEX` | X4.15 `-INDEX` |
| 16 | `DIR` | X4.16 `-DIR` |
| 17 | absent | processor-only X4.17 `-H.LOAD` |
| 18 | `W.GATE` | X4.18 `-WR.GATE` |
| 19 | `M.ON` | X4.19 `-MOTOR.ON` |
| 20 | `S.SEL` | X4.20 `S.SEL` |
| 21 | `SEL.1` | X4.21 `-D.SEL1` |
| 22 | `SEL.0` | X4.22 `-D.SEL0` |
| 23 | `RD.DATA` | X4.23 `RD.DATA` |

The НГМД table omits polarity bars, while the processor sheet shows the
active-low interface senses produced or received by its inverting buffers.
The shared names and contact numbers agree; the spelling difference is not a
reason to invert the cable again.

## Drive-mechanism fanout

Both ЕС5323 mechanisms use the same `X2` signal contacts. Odd contacts are
grouped returns; the active signals use the standard even contacts:

| Drive X2 | Signal | Intermediate contact |
| ---: | --- | ---: |
| 8 | `INDEX` | 1 |
| 10 | `SEL.0` | 2 |
| 12 | `SEL.1` | 3 |
| 16 | `M.ON` | 4 |
| 18 | `DIR` | 5 |
| 20 | `STEP` | 6 |
| 22 | `W.DATA` | 7 |
| 24 | `W.GATE` | 8 |
| 26 | `TR.0` | 9 |
| 28 | `W.PROT` | 10 |
| 30 | `RD.DATA` | 11 |
| 34 | `RDY` | 12 |
| 1/3/5/7 | GND group | 13 |
| 9/11/13/15 | GND group | 14 |
| 17/19/21/23 | GND group | 15 |
| 25/27/29/31/33 | GND group | 16 |
| 32 | `S.SEL` | 17 |

Drive power is separate: each assembly's `X1` carries +12 V, GND, and +5 V.
It does not come from processor X4.12/.13.

## Source-model divergences

The recovered primary drawing invalidates four inference-era assignments in
the current source model:

1. D100 is not the CPU-data-to-D93-DAL transceiver. It is the drive-output
   КР580ВА87 whose B-side pins 16,19,18,14,15,17,13,12 feed X4.10,.16,.9,
   .11,.18,.17,.19,.20 respectively. The existing `FDC_DAL0..7` attachment
   and D100 `/OE`/`T` bus-control narrative must be removed or reassigned.
2. D28 pins 2 and 4 feed X4.21 `-D.SEL1` and X4.22 `-D.SEL0`, not the stale
   `.006` X4.5/X4.4 tape labels. D28 pins 5/6 are used in the READY receive
   path, so they are not NC on the `.009` board.
3. X4.6-.23 are no longer anonymous landing boundaries. Sheet 3 supplies the
   circuit names and local endpoints above. X4.2-.5 remain a cross-revision
   disposition item because sheet 3 omits them while the НГМД XS5 side groups
   contacts 1-6 as returns.
4. D93 DAL0-DAL7 are the direct sheet-1 D0-D7 bundle. D26 PC2/PC4/PC5/PC6
   feed MOTOR EN, FM/MFM, D_SEL, and S.SEL respectively. In particular,
   D28.9 is part of the read-separator inverter on sheet 3, not a branch of
   the D26-PC4/DDEN conductor.

These corrections precede another routed-board refresh. They do not authorize
guessing external cable conductors for X4.1-.5 or the still-untraced source of
the D100 pin-9/pin-11 control continuation.
