# macOS diagnostic-host acceptance on CS00015

Date: 2026-08-06
Board: Arvutimuuseum Juku `CS00015`
ROM: exact T32 `1B/D62B`
Host: macOS, CP2102 at `/dev/cu.usbserial-0001`, built-in Apple CP210x driver

## Retained result

The Python diagnostic host ran on the recorded macOS setup without pyserial,
a vendor Silicon Labs driver, or a platform patch. `host.py` uses stdlib
`termios`; the session established correct 2400-baud operation with the
built-in `AppleUSBSLCOM.dext` driver. The observed device was
`/dev/cu.usbserial-0001`. Use the adapter's `cu.*` node for outbound contact
and confirm its actual name on the bench; this capture does not establish
compatibility with every macOS release or adapter.

This record qualifies the named T32 diagnostic session. CS00015 later moved
to network firmware; see [its service record](../../docs/cs00015-service-record.md)
for the fitted configuration. For production network-host use, see
[the bootstrap guide](../../docs/janet-fastboot.md).

One cold boot decoded the exact T32 identity `1B/D62B` with the expected
CS00015-era bitmap: PIC, PPI, D54, D57 and both compact RAM windows passed,
with the known T31-family D55 artifact bit `08` (see
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md);
that bit is produced by the exact T31/T32 firmware on a clean board and is not
board evidence). A subsequent control-only attach and a complete smoke
application session then passed with zero handshake mismatches and zero store
retries.

## Sessions

| Capture | Result | Supported claim |
| --- | --- | --- |
| `sessions/macos-first-contact/20260806T094437.578482Z.*` | error, attach timeout, 0 bytes both directions | attach timed out with no observed traffic; this capture does not identify the board state |
| `sessions/macos-t32-attach/20260806T111703.706101Z.*` | error, attach timeout, 35 bytes received, 0 sent | negative evidence only: attach against a freshly reset board leaves the ROM banner unanswered until its handshake fails |
| `sessions/macos-t32-coldboot/20260806T112016.594609Z.*` | ok | full cold boot, exact `1B/D62B`, bitmap `08`, zero mismatches |
| `sessions/macos-t32-attach2/20260806T112113.469673Z.*` | ok | control-only reattach to the resident loader after the cold boot |
| `sessions/macos-smoke/20260806T112418.835712Z.*` | ok | verified 134-byte `smoke-4000.bin` upload, CALL, `A=0Ch`, result `534D4F4B00` + `55` fill at `4100h` |

The failed attaches establish the entry requirement. `--attach-loader`
requires a resident loader; it does not perform the cold diagnostic banner
handshake. With a cold T32 diagnostic ROM, complete a full session before
reattaching without RESET. Service ROMs with an explicit `J` loader entry have
a separate setup described in [the diagnostic guide](README.md).

The macOS smoke session and Linux control both had zero store retries and
handshake mismatches. These captures qualify the recorded identity, verified
upload/readback, and transport behavior; they do not qualify throughput.

## Relevance to CS00024

These sessions qualify this macOS/T32 setup. The CS00024 work
recorded in [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md) ran from the Linux
bench. For a macOS rerun, select the actual `cu.*` device with `--port` in
[`batch.py`](batch.py) or [`host.py`](host.py), and match the firmware identity,
baud and entry mode required by the chosen diagnostic. The historical device
name and T32 identity above are evidence from this session, not universal
bench defaults.
