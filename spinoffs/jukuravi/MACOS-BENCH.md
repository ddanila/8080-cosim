# macOS diagnostic-host acceptance on CS00015

Date: 2026-08-06
Board: Arvutimuuseum Juku `CS00015`
ROM: exact T32 `1B/D62B`
Host: macOS, CP2102 at `/dev/cu.usbserial-0001`, built-in Apple CP210x driver

## Retained result

The Python diagnostic host ran on the recorded macOS setup without pyserial,
a vendor Silicon Labs driver, or a platform patch. `host.py` uses stdlib
`termios`; the session established correct 2400-baud operation with the
built-in `AppleUSBSLCOM.dext` driver. Use the adapter's actual `cu.*` node for outbound contact. This capture
does not establish compatibility with every macOS release or adapter.

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

## Qualification evidence

| Capture | Supported result |
| --- | --- |
| [Cold boot](sessions/macos-t32-coldboot/20260806T112016.594609Z.json) | Exact `1B/D62B`, bitmap `08`, zero handshake mismatches |
| [Reattach](sessions/macos-t32-attach2/20260806T112113.469673Z.json) | Control-only attach to the resident loader after cold boot |
| [Smoke upload](sessions/macos-smoke/20260806T112418.835712Z.json) | Verified 134-byte `smoke-4000.bin`, CALL/RET with `A=0Ch`, and `534D4F4B00` plus `55` fill at `4100h`; zero store retries |

`--attach-loader` requires a resident loader; its implementation waits for
loader request tokens and does not perform the cold diagnostic banner
handshake. With a cold T32 diagnostic ROM, complete a full session before
reattaching without RESET. Service ROMs with an explicit `J` loader entry have
a separate setup described in [the diagnostic guide](README.md).

The smoke payload is the historical 134-byte image identified by the capture’s
SHA-256 and readback frames; the current `smoke-4000.bin` has changed.

The macOS smoke session and Linux control both had zero store retries and
handshake mismatches. These captures qualify the recorded identity, verified
upload/readback, and transport behavior; they do not qualify throughput.

## Running another diagnostic

Select the actual `cu.*` device with `--port` in [`batch.py`](batch.py) or
[`host.py`](host.py), and match the firmware identity, baud and entry mode
required by that diagnostic. The [CS00024 captures](CS00024-PHYSICAL.md)
were made on Linux and do not extend this macOS qualification.
