# Stock-ROM fast bootstrap

Status: **CS00015 PHYSICALLY PROVEN / CS00014 BENCHMARK PENDING**

The fast path preserves an unmodified EktaSoft Janet 1.2 ROM. The stock client
first loads `cpmish/juku-fastboot-stage1.bin` at 0100h using its ordinary
9600/8O1 protocol. The 558-byte stage masks interrupts, takes exclusive
ownership of D57 channel 0 and D11, selects the CS00014/CS00015-proven
19200/8O1 mode-2/count-4 clock, and receives the CP/M resident image directly
at B400h-CDFFh. It then jumps to the normal CA00h BIOS entry.

This is intentionally a single-client, fixed-layout CP/Mish protocol. Avoiding
general address/length negotiation keeps the stock-loaded stage to five
128-byte records. The normal `janet_netboot.py` path remains byte-for-byte
unchanged and can still boot all five preserved systems.

## Wire contract

All multibyte CRCs are big-endian CRC16-CCITT (polynomial 1021h, initial
FFFFh). Short control frames finish with an XOR byte which makes the XOR of the
complete frame zero.

| Direction | Frame | Meaning |
| --- | --- | --- |
| target to host | `J R 01 0D xor` | stage ready, protocol 1, thirteen blocks |
| host to target | `J H 01 0D crc-hi crc-lo xor` | session header and whole-image CRC |
| host to target | `J B seq 512-data crc-hi crc-lo` | one protected block; CRC covers sequence and data |
| target to host | `J A seq status xor` | ACK/status; sequence FFh acknowledges the header and 0Dh is final verification |

Status 0 accepts, 1 reports a block CRC failure, 2 reports final whole-image
CRC failure, and 3 reports an unexpected sequence. The target searches for the
two-byte magic after bounded receive timeouts. A valid duplicate of the
previous block is verified and ACKed without advancing, so a lost target reply
is safe. The host retries a block up to five times by default. A reset always
returns to the stock ROM, allowing the operator to retry either the fast path
or the untouched all-stock path.

## Use

Build the stage and network system in the CP/Mish checkout, then serve the
usual A: and optional B: volumes with one extra option:

```sh
cd ~/fun/cpmish && make juku-fastboot-stage1.bin \
    juku-net-mode2-system.bin juku-net-mode2.img
cp juku-net-mode2.img cs00015-fastboot.img
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-stage1.bin --disk-baud 19200 \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

Power/reset the stock-ROM machine and type `TN` without Enter, as for the
ordinary Janet boot. The host learns the one active station pair from that
request. Do not use `--fast-stage1` with a disk baud other than 19200.

## Verification and expected speed

`make juku-fastboot-cosim-check` in CP/Mish executes the assembled 8080 stage,
checks the D57 mode/count writes, compares all 6656 installed bytes, and stops
at CA00h. A second run corrupts one block, drops one complete block, duplicates
another, and discards one valid target ACK. It reaches the same byte-exact
handoff with exactly the three necessary host retries; duplicates are
idempotent. The host-side framing and
CRC vector are also pinned by `tests/janet_fastboot_protocol_test.py`.

Freeze the 2026-08-14 CS00015 comparison as two named physical baselines. Both
used the same CP/Mish mode-2 system, host volume, cable, and machine. Timing
starts at the first checksum-valid Janet request and ends at the first valid
network A: request, so operator delay is excluded:

| CS00015 baseline | First disk request | Stock frames | Detail |
| --- | ---: | ---: | --- |
| **Fast stage v1** | **17.508 s** | 42 | stage 7.99 s; bulk 8.90 s; one recovered block-0 timeout |
| **Original stock 9600** | **73.873 s** | 330 | 6784 bytes / 53 records |

Both runs reached the visible CP/M prompt. Fast stage v1 saved 56.365 seconds,
a **4.22x speedup** or **76.3% reduction**. These values are retained as
baselines; later stage, guard, window, compression, or clock experiments must
be recorded as separate variants rather than replacing them. The raw
19200/8O1 wire floor for 6656 data bytes remains about 3.8 seconds. The
machine-readable record is
`evidence/juku-serial/cs00015-fastboot-20260814.json`.

Further worthwhile measurements are, in order:

1. ten cold/warm runs on CS00014 and CS00015, recording stage, bulk, total,
   retries, rejects, and Linux UART counters;
2. profile the final bitwise CRC scan and the conservative 20 ms turn guard;
3. reduce the stage below 512 bytes only if one fewer stock record measurably
   matters;
4. compare stop-and-wait with a two-block window only after fault recovery is
   equally deterministic;
5. evaluate compression only end-to-end. The current image shrinks from 6656
   to about 4840 bytes with desktop DEFLATE, but simple PackBits reaches only
   6195 bytes, so decoder size and 8080 time can easily consume the wire saving;
6. keep nominal 38400 mode-2/count-2 as a separately recoverable experiment,
   never a default before multi-board physical proof.

The current cosim does not yet automate power-reset/restart during a block.
Reset recovery is structurally safe because the stock ROM regains control, but
an automated host re-discovery test remains before declaring the path fully
bench-qualified.

A direct stock transfer to B400h was also tested as a possible zero-stage
shortcut. The stock client reached the requested CA00h execute address but did
not install the records at B400h (6327 of 6656 bytes differed in cosim). The
existing low-memory staging premise is therefore necessary; merely changing
the Janet record addresses is not a valid optimization.
