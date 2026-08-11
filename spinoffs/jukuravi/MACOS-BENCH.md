# macOS host first contact on CS00015

Date: 2026-08-06
Board: Arvutimuuseum Juku `CS00015`
ROM: exact T32 `1B/D62B`
Host: macOS, CP2102 at `/dev/cu.usbserial-0001`, built-in Apple CP210x driver

## Retained result

The unmodified Linux-developed host stack ran on macOS with no installation:
no pyserial, no vendor Silicon Labs driver, no code change. `host.py` uses
stdlib `termios`, which sets 2400 baud correctly on Darwin, and macOS ships
its own CP210x driver (`AppleUSBSLCOM.dext`). The adapter enumerates as
`/dev/cu.usbserial-0001`; the `cu.*` node must be used because `tty.*` blocks
on carrier detect, which this link never asserts.

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
| `sessions/macos-first-contact/20260806T094437.578482Z.*` | error, attach timeout, 0 bytes both directions | negative evidence only: `--attach-loader` without a resident loader produces no traffic and times out |
| `sessions/macos-t32-attach/20260806T111703.706101Z.*` | error, attach timeout, 35 bytes received, 0 sent | negative evidence only: attach against a freshly reset board leaves the ROM banner unanswered until its handshake fails |
| `sessions/macos-t32-coldboot/20260806T112016.594609Z.*` | ok | full cold boot, exact `1B/D62B`, bitmap `08`, zero mismatches |
| `sessions/macos-t32-attach2/20260806T112113.469673Z.*` | ok | control-only reattach to the resident loader after the cold boot |
| `sessions/macos-smoke/20260806T112418.835712Z.*` | ok | verified 134-byte `smoke-4000.bin` upload, CALL, `A=0Ch`, result `534D4F4B00` + `55` fill at `4100h` |

The two failed attaches are chronology of the same host-side mistake, not
hardware findings. `--attach-loader` means "reattach to an already-resident
loader without resetting"; it deliberately stays silent and never answers the
boot banner. Against a cold or freshly reset board the ROM's handshake times
out into its failure tone. That tone is the host's fault. On a cold boot, run
a full session first, then attach as often as needed without another RESET.
The rule is documented in [`README.md`](README.md).

## Timing note

The five verified smoke chunks took 35.29 seconds against the 32.758 seconds
recorded for the same image on the Linux host in
[`T31-PHYSICAL.md`](T31-PHYSICAL.md). Both runs had zero store retries and
zero handshake mismatches. The difference is host-side timer granularity
around the 6 ms response guard, not link degradation. Judge link health by
`store_retries` and `mismatches`, never by wall-clock; do not compensate by
raising `--loader-guard-ms` or `--loader-votes`.

## Relevance to CS00024

These sessions prove the host platform, not the board: the CS00024 work
recorded in [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md) ran from the Linux
bench. When CS00024 (or any board) moves to the macOS bench, the same
serial-port and cold-boot rules apply unchanged, and
[`batch.py`](batch.py)/[`host.py`](host.py) need only the `--port
/dev/cu.usbserial-0001` argument.
