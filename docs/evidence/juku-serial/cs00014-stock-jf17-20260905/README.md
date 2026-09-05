# CS00014 stock-ROM JF17 reset recovery — 2026-09-05

Physical CS00014, owner-confirmed stock ROM, station 09, connected to native
macOS `jukuhost 0.4.0-m8` through `/dev/cu.usbserial-110`. All boot and NetDisk
phases used 9600/8O1. A: was the read-only CP/M Plus recovery volume; no B: was
attached. The operator selected T → N after each hardware reset.

The first attempt completed JF17 but left a blank screen after `Load 01`,
with zero NetDisk requests. The stock adapter's CP/M startup still programmed
D57 count four (19200), despite the separate NETINIT path and loader selecting
count eight (9600). The corrected NETWORK9600 CP/M handoff programs count
eight too. `failed-first.log` records the unsuccessful attempt.

With the corrected image, one unchanged host process (PID 38439):

- recognized the already-waiting Janet poll and booted to `A>`;
- completed remote `DIR` and returned to `A>`;
- recognized the operator's hardware reset and T → N as a checked Janet poll
  during NetDisk, then automatically performed a second complete JF17 boot;
- returned to `A>` and completed another remote `DIR`.

The closed capture records 1144 requests, 44 disk reads / 132 records, zero
writes, zero retries, zero UART errors, one target reset and one bootstrap
restart. Both Janet transfers had zero rejects and both JF17 extensions had
zero retries. The operator confirmed the first corrected physical CP/M prompt;
`console.bin` records both banners and both directory listings.

After closing that capture, a replacement host (PID 39110) passively recognized
an existing NetDisk request, resumed the running CP/M session without bootstrap,
and completed another `DIR`. `reconnect.log` records classification and
`reconnect-console.bin` records that command. The replacement host was left
running with recovery enabled.

Validation: native warning-clean build and startup selftest, runner test,
stock artifact test, an artifact mutation reproducing the count-four regression
(rejected), and the full two-boot stock recovery simulator test passed. The
simulator timeout now allows 90 seconds for Janet, 9600 transfer and CCP reads
on macOS; PTY serial links alone do not detect a physical baud mismatch.

`boot.json` binds the exact corrected system and JF17 hashes. `host.cap` is the
closed CRC-protected capture, `host.log` its summary, and `requests.jsonl` the
converted request evidence. This run qualifies boot, hardware-reset recovery
with manual stock-ROM network selection, and live host replacement. It does
not qualify reset during an incomplete transfer, power cycling, disk writes,
or broader diagnostics.
