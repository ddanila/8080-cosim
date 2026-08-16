# Stock-ROM fast bootstrap

Status: **V6 FASTEST EXACT PHYSICAL TIMING; V7 PHYSICALLY QUALIFIED; V8
SIMULATION-QUALIFIED OVERLAP CANDIDATE; V4 RATE FAILED; 19,200 FROZEN**

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

Protocol v2 retains the same frames and fixed layout. Its block CRC field is
the cumulative CRC16 of all image data through that block rather than an
independent CRC of `sequence + data`. The target checkpoints the cumulative
CRC after every accepted block and retains the preceding checkpoint for a
duplicate. Corruption or loss therefore retries safely, while the thirteenth
accepted block already proves the header's whole-image CRC; no second B400h-
CDFFh scan is required. The ready/header version byte distinguishes v1 and v2,
and the host negotiates either from the stage marker.

Protocol v3 is a deliberately separate streaming path. Its 384-byte build
artifact contains a one-record core followed by a padded extension:

| Direction | Frame | Meaning |
| --- | --- | --- |
| host to target | `A5 3A 256-extension sum1 sum2` | high-speed extension protected by end-around-carry Fletcher sums |
| target to host | `J R 03 01 xor` | extension ready for one system stream |
| host to target | `J S 6656-system crc-hi crc-lo` | fixed resident image and CRC-16/IBM (A001h, initial 0000h) |
| target to host | `J A 00 00 xor` three times | verified image accepted; target will enter CA00h |

Only the 128-byte core is sent through stock Janet at 9600. It selects the
already proven 19200/8O1 clock and authenticates the 256-byte extension in low
RAM. The extension then receives the whole fixed image without per-block
turnarounds. A bad extension or system stream is ignored and the host retries
it in full; v1/v2 remain the finer-grained recovery alternatives.

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

The frozen physical baseline command above uses `juku-fastboot-stage1.bin`
(protocol v1). The next distinct candidate is **Fast stage v2**:

```sh
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v2.bin --disk-baud 19200 \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

The physically proven **Fast stage v3** uses the identical command with the new
bundle; it does not require a ROM burn:

```sh
cd ~/fun/cpmish && make juku-fastboot-v3.bin
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v3.bin --disk-baud 19200 \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

The physically proven artifact is 384 bytes (117-byte core padded to 128 plus a
172-byte extension padded to 256), SHA-256
`bf5104c3d7af271a52defa54acf7773daf032461ff303cc04f0fe4e5ba49b22a`.

## Verification and expected speed

`make juku-fastboot-cosim-check` in CP/Mish executes the assembled 8080 stage,
checks the D57 mode/count writes, compares all 6656 installed bytes, and stops
at CA00h. A second run corrupts one block, drops one complete block, duplicates
another, and discards one valid target ACK. It reaches the same byte-exact
handoff with exactly the three necessary host retries; duplicates are
idempotent. The host-side framing and
CRC vector are also pinned by `tests/janet_fastboot_protocol_test.py`.

V3 adds its own clean and injected-fault cases. The clean run uses only one
stock data record, installs B400h-CDFFh byte-exact, and reaches
CA00h. The fault run rejects a corrupted extension, rejects a corrupted full
system stream, recovers after a completely lost stream, and accepts the second
of three success frames when the first is hidden from the host. It reaches the
same byte-exact entry with one extension retry and two stream retries.

The first CS00015 attempt authenticated the extension but exposed a Linux host
queue assumption: after accepting several kilobytes, the USB serial driver did
not advertise more write room within the generic one-second limit. The target
correctly remained in its stream receiver. V3 now grants only its long stream
a ten-second *stall allowance* (not a ten-second delay); short Janet and disk
frames retain the one-second guard. The reset/retry then passed with 18 stock
frames, zero extension/stream retries, a 2.21-second stock stage, 4.13-second
high-speed phase, and the first valid A: request at 6.915 seconds. The operator
confirmed the visible CP/M prompt.

## Fast stage v4: negotiated 28,800

The first post-v3 rate candidate is **28,800**, not 25,600. The classic CP2102
uses the discrete AN205 rate table; the current Linux
[`cp210x` driver](https://github.com/torvalds/linux/blob/master/drivers/usb/serial/cp210x.c)
lists 19,200 followed by 28,800 and quantizes requests through those table
boundaries. A nominal 25,600 request therefore does not produce 25,600 on this
adapter. The Juku can produce about 28,622.5 baud from 16 MHz / 13 / 43 with
D57 mode 2/count 43 and D11 x1. Its -0.62% mismatch against 28,800 is modest,
the 28.6 kHz x1 input is below the КР580ВВ51А's documented 64 kHz x1 ceiling,
and the external CP2102/RS-232 chain is already proven well above this rate.

V4 remains a one-stock-record design. Its 123-byte core loads a 381-byte
extension padded to 384 bytes at proven 19,200. The extension announces
`J R 04 02 xor`; the host requests the experiment at 19,200, drains those bytes,
and switches to exact 28,800 through Linux `termios2/BOTHER`. The target sends
`J Q 04 01 xor` at the candidate rate, requires the matching `J K 04 01 xor`
from the host, and only then announces stream readiness. If either direction
fails, the target restores 19,200 and repeatedly exchanges the acknowledged
`J Q/K/R 04 00` fallback sequence. A missing or quantized host custom rate is
also caught by exact readback and enters this same fallback. After the stream,
both ends restore 19,200 before NETROM2 requests its `NR` marker.

The separate `juku-fastboot-v4.bin` artifact is 512 bytes and has SHA-256
`15c016492e7a3ec8f8e1666b387ec1f1a74b7f932b087b1bd21a22bd9be0ab9e`.
Clean 28,800, corruption/loss/lost-reply, and forced high-rate failure paths
all reach CA00h with B400h-CDFFh byte-exact in cosim; the forced failure uses
the acknowledged 19,200 fallback. V1-v3 hashes remain unchanged. The raw
6656-byte stream floor falls from 3.813 s at 19,200 to 2.542 s at 28,800.
Accounting for the 128-byte larger extension and negotiation guards predicts a
CS00015 first-disk request near **5.8 seconds**, roughly another 1.1 seconds
below v3. The attached Silicon Labs CP2102 (`10c4:ea60`) subsequently passed
exact 28,800/8O1 `termios2` readback and restored 19,200/8O1 without sending
target bytes.

The first physical CS00015 v4 run did **not** complete the 28,800 negotiation.
Its acknowledged fallback worked exactly as designed: the target and host
returned to 19,200, the 6656-byte CRC was `5313`, extension and stream retries
were both zero, the first A: request arrived at 9.199 seconds, and the operator
confirmed the prompt. The split was 3.77 seconds through the stock stage and
4.95 seconds through extension, negotiation/fallback, and stream. This is
2.284 seconds (33.0%) slower than v3, so v4 was rejected as a default and
remains diagnostic evidence rather than a speed improvement on CS00015.

This result also reinforces the prior x1 evidence: exact host 28,800 was
verified, target mode-2/count-43 is in spec and differs by only -0.62%, yet the
bidirectional x1 exchange did not complete. The original run logged only the
eventual fallback, so it cannot identify which direction failed. The host now
logs whether the target-to-host probe arrived and, if it did, whether the
host-to-target ACK/final-ready exchange completed. No rate conclusion should
be made more specific than “x1 negotiation failed” until that leg is captured.

Decision: freeze **19,200 mode-2/count-4 x16** as the stock-hardware fastboot
clock. Its approximately 307.7 kHz D11 input is already near the documented
310 kHz x16 ceiling. The only in-spec route materially above it uses x1 and
failed here; 38,400/count-2 x16 would drive about 615 kHz, roughly two times
over specification. A v4 repeat is useful only to locate the failed direction,
not as a likely optimization. Subsequent speed variants retain 19,200 and test
8N1, compression with measured 8080 decode cycles, or stock-Janet latency.

## Fast stage v5: 19,200/8N1

V5 isolates framing while retaining v3's proven D57 mode-2/count-4 x16 clock,
one-record core, Fletcher-protected 256-byte extension, CRC-16/IBM stream, and
full-stream retry behavior. The core selects D11 mode `4Eh` (8N1), the host
switches only the bootstrap extension/stream to 8N1, and the extension drains
its three success replies before restoring mode `5Eh` (8O1). NETROM2 and its
host disk remain unchanged at 19,200/8O1.

`juku-fastboot-v5.bin` is 384 bytes: 117 bytes of core padded to 128 and 197
bytes of extension padded to 256. Its SHA-256 is
`8fa63db50daaf64f8da9025b443cbe0cb3802d985a4ba5c74630435953d628a4`.
Clean and corruption/loss/lost-reply cosim paths exercise mode `4E`, install
B400h-CDFFh byte-exact, restore mode `5E`, and enter CA00h. V1-v4 hashes remain
unchanged. Removing the parity bit lowers the 6656-byte wire floor from 3.813
to 3.467 seconds and predicted the first CS00015 A: request near **6.55
seconds**, only about 0.35 seconds below v3. Earlier mode-3 BAUDTEST evidence
had not sustained long 19,200/8N1 receives, making physical qualification the
decisive gate; reset plus v3 remained the fallback.

The physical CS00015 run then matched that prediction: one 128-byte stock
record and the 256-byte extension completed with zero retries, the CRC-valid
6656-byte stream completed with zero retries, and the first A: request arrived
at **6.551 seconds**. The split was 2.23 seconds through the stock stage and
3.84 seconds through the extension plus 8N1 stream. This saves 0.364 seconds
(5.3%) over physical v3 and made v5 the fastest uncompressed variant while
retaining v3 byte-for-byte as the proven 8O1 fallback.

## Fast stage v6: 19,200/8N1 plus ZX0

V6 combines the physically proven v5 clock/framing path with ZX0 classic
compression. Its stock-loaded core remains one 128-byte record. The core
authenticates a 384-byte high-speed extension containing Ivan Gorodetsky's
92-byte Intel 8080 ZX0 decoder; the host then sends a length-bounded 4826-byte
compressed stream protected by CRC-16/IBM. The target authenticates the
compressed representation before decoding it to B400h-CDFFh, restores 8O1,
and enters CA00h. A corrupt stream is never decoded.

`juku-fastboot-v6.bin` is a self-contained 5342-byte host artifact: a 120-byte
core padded to 128, a 313-byte extension padded to 384, a four-byte payload
descriptor, and the 4826-byte compressed system. Only the core, extension, and
compressed packet travel; the artifact embeds the original system CRC so the
host refuses to pair it with a different resident image. Its SHA-256 is
`74826eeb5e95feb6b9f1bed7d7b5957447166a7f3ac2722633e4cff7768babf0`.
The build vendors the BSD-3-Clause ZX0 v2.2 compressor and deterministically
regenerates the payload. V3 and v5 remain byte-identical at their frozen
hashes.

Clean and injected-fault cosim paths verify all 6656 decompressed bytes,
reject a corrupt extension and compressed stream, recover from a completely
lost stream, tolerate a lost success reply, restore D11 mode `5Eh`, and enter
CA00h. Physical CS00015 then passed with zero retries: 2.21 seconds through the
stock stage, 3.53 seconds through the extension, compressed stream, and decode,
and the first A: request at **6.214 seconds**. The visible prompt and network
`DIR` both worked. V6 saves 0.337 seconds (5.1%) over v5, 0.701 seconds (10.1%)
over v3, and 67.659 seconds (91.6%, 11.89x) over Original stock 9600.

## Fast stage v7: fixed authenticated stream metadata

V7 keeps v6's physically proven one-record stock core, 19,200/8N1 clock and
framing, ZX0 payload, and authenticate-before-decode rule. It moves the fixed
compressed length and expected compressed CRC into the Fletcher-protected
extension, reuses the core's RX routine at 016Eh, and lets CP/M's immediate
`NETINIT` perform the normal 8O1 setup at CA00h. These changes fit the
extension in **256 rather than 384 bytes**. The wire stream is simply `J Z`
followed by the fixed 4826-byte payload; four redundant length/CRC bytes also
disappear.

`juku-fastboot-v7.bin` is a 5218-byte self-describing host artifact: 128-byte
core, 256-byte extension, eight-byte `Z7` descriptor, and 4826-byte compressed
system. The descriptor binds the artifact to the uncompressed system CRC,
compressed length, and compressed CRC; the host validates all three before
sending anything. Its simulation-qualified SHA-256 is
`bc3897d6d79cfaafd4b747aecc60410b9b1eec6c9296565176c23f38c9677b88`.

Clean and injected-fault cosim runs reject a corrupt extension and compressed
stream, recover from total stream loss and a lost success reply, reproduce all
6656 bytes at B400h-CDFFh, and preserve the frozen v3/v5/v6 hashes. A separate
end-to-end run continues beyond CA00h: the real CP/M BIOS changes D11 from v7's
mode `4Eh` to resident mode `5Eh`, reaches `A>`, and completes network `DIR`
with 34 reads and zero retries. V7 also reduces the host's post-success handoff
guard from 80 to 20 ms because its short drain plus BIOS-owned reinitialisation
replace v6's longer extension drain. One fewer 128-byte extension record, four
fewer stream bytes, and the 60 ms guard reduction predict about **0.129 s**
below v6, or roughly **6.09 s** to the first A: request on CS00015. A physical
CS00015 run on 2026-08-15 passed the stock-ROM bootstrap, 19,200 handoff,
visible prompt, and network `DIR`, qualifying v7's complete functional path and
short handoff guard. Its exact first-disk timestamp was not retained, so this
value remains a prediction. At that stage v6 remained the fastest timed
physical baseline; later v12 repeats supersede it at 5.739-5.740 seconds.

## Fast stage v8: interrupt-fed receive/decode overlap

V8 retains v7's one stock record, fixed 4826-byte ZX0 stream, CRC-16/IBM,
19,200/8N1 framing, bounded output, and complete-stream retry policy. Its
separate 640-byte extension overlaps reception and decoding instead of waiting
for all compressed bytes before starting ZX0.

D11 RxRDY reaches PIC IR2. Entering a downloaded stage without returning from
stock Janet makes the ordinary RomBios dispatcher both stateful and too slow
for one interrupt per 884 modeled CPU cycles, so v8 saves the first three
writable bytes at `D79Fh` and temporarily replaces them with a jump to a
minimal single-source trampoline. That trampoline preserves the interrupted
register set, reads D11, issues 8259 EOI, and returns directly to the decoder.
The original `D79Fh` bytes are restored verbatim before CP/M starts.

The ISR appends the fixed stream at 4000h, maintains the compressed CRC, and
records D11 errors. The host sends `JZ`, waits 2 ms for the atomic handoff, and
then sends the payload. ZX0 starts once 256 bytes are buffered and consumes the
same linear area while the ISR fills its tail. Execution remains gated by all
of the following:

- exact 4826-byte receive completion and CRC `7A91h`;
- no USART error;
- exact final compressed pointer `52DAh`;
- exact decompressed output boundary `CE00h` with every write fenced below it;
- restoration of the saved RomBios dispatcher before the success reply.

A malformed decoder can abandon nested calls through a saved session stack,
drains the fixed remainder, and returns to `JZ` search. Clean and injected
fault cases reject a damaged extension and compressed stream, recover from a
wholly lost stream and lost first success reply, and install B400h-CDFFh
byte-exactly. The full continuation restores D11 from mode `4Eh` to BIOS mode
`5Eh`, reaches `A>`, performs network `DIR` with 34 reads and zero retries, and
asserts the original `D79Fh` bytes.

`juku-fastboot-v8.bin` is 5602 bytes: 128-byte core, 640-byte extension,
eight-byte `Z8` descriptor, and the unchanged 4826-byte payload. SHA-256 is
`ae89fef7dcce9d6ffd329e0862af9be16710c4b703ff9c0a3c444aa184c34c78`.
The pinned 1.70 MHz cosim measures 1,010,204 cycles (0.594 s) from v7's final
compressed byte to CA00h and 203,037 cycles (0.119 s) for v8. Charging v8 for
three extra 128-byte extension records (0.200 s at 884 cycles/byte) and its
2 ms marker gap leaves a deterministic **273 ms projected gain**. This is a
desk result, not a physical timing claim; v8 needs a logged CS00015 run.

### Compact stock execute policy

The native NETD capture pads its final `0Fh` execute service to 127 logical
bytes and carries it as three Janet fragments. The unmodified `ekta37` client
also accepts the canonical single-fragment logical message `03 0F`: `03h` is
the start-and-end fragment marker and `0Fh` is the complete service body. The
optional host policy `--compact-stock-execute` uses that representation only
for fastboot; the byte-exact captured form remains the default for ordinary
stock boot and for comparison.

For a one-record core this changes the clean host count from 18 to 14 frames.
The encoded bootstrap messages fall from 340 to 198 bytes, and removing two
now-unneeded destination-zero line turns saves another 12 bytes: **154 serial
bytes**, whose 9600/8O1 wire floor is about **176 ms**. Combining that floor
with v8's earlier 5.82-second projection suggests roughly **5.64 seconds** to
the first A: request, but only a logged physical run may claim the gain. This
policy also makes the existing 50 ms pre-rate-change guard sufficient for the
entire final 21-byte turn/execute/turn sequence instead of relying on USB-UART
queue behaviour for NETD's padded tail.

Clean, extension/stream-fault, and complete CP/M continuations pass with the
compact form. The latter reaches `A>`, completes `DIR` with 34 reads and zero
disk retries, restores D11 to `5Eh`, and restores the temporarily patched
RomBios bytes. Two negative experiments delimit the safe shortening: omitting
the `06h` end descriptor or shortening its fixed eight-byte descriptor prevents
the stage from announcing readiness. Those structures therefore remain
unchanged.

## Fast stage v9: polled marker and exact-length extension

V9 keeps v8's interrupt-fed payload, concurrent native ZX0 decode, fixed
4826-byte CRC-protected stream, 256-byte producer lead, retry policy, output
fence, and temporary RomBios dispatcher. It removes interrupts from the idle
two-byte `JZ` search: the extension polls those bytes through the core's
existing receiver, then unmasks IR2 only for payload bytes. Before arming the
payload it deliberately services the PIC request latched by the polled `Z`;
the existing 2 ms host gap makes that drain deterministic. This removes the
marker ring, its producer/consumer state, and the payload/idle branches from
the hot ISR.

The resulting extension is **556 bytes**. V9's core carries an exact 16-bit
extension length instead of a count of padded 128-byte records, so all 556
bytes and no 640-byte padding travel at 19,200. The self-contained
`juku-fastboot-v9.bin` is 5518 bytes and has SHA-256
`7dd745e67ac400c22a229a796e77dd51239df793ec5375bf9ebc6bd8069de924`.
The v8 artifact remains byte-exact at its published hash.

Clean and injected-fault cosim reject corrupt extension/stream data, recover
from a lost stream and lost success reply, and reproduce B400h-CDFFh exactly.
The full continuation reaches `A>`, performs `DIR` with 34 reads and zero disk
retries, restores D11 to `5Eh`, and restores `D79Fh`. V9 measures 78,667 cycles
from the last compressed byte to CA00h, versus v8's 203,037. Including its
300-byte extension delta over v7 and the common 2 ms marker gap, it saves a
modeled **390 ms over v7** and **117 ms over v8**. Adding the compact stock
execute wire floor to the prior v7 estimate projects about **5.52 seconds** to
the first A: request.

On 2026-08-15 physical CS00015 completed this exact v9 artifact using
`--compact-stock-execute` and the conservative default guards. It reached the
visible CP/M prompt, then completed network `DIR`. This qualifies v9, compact
stock execute, the 19,200 handoff, resident 8O1 restoration, and subsequent
Janet disk traffic as one real-hardware path. No exact first-request timestamp
was retained, so 5.52 seconds remains a desk projection and the low-latency
guard policy below remains a separate physical candidate.

A post-qualification instruction audit deliberately did not replace this
artifact. Removing the payload ISR's unconditional exit jump shortened the
routine by three bytes but made the first overlapped decode fail
deterministically: the received compressed input and CRC were exact, while the
decoded output was not; a retry succeeded only because the whole input was
then resident. The saved ISR cycles let the decoder consume the fixed 256-byte
lead too soon. Restoring the jump recovered every clean, fault, and `DIR` test.
Other static rearrangements produced a 5505-byte desk variant, only about
6.8 ms less wire time, but changing the now physically qualified v9 hash for
that marginal unmeasured gain is not justified. Preserve the published hash;
if revisited, give the smaller artifact a new version and physical test.

### Low-latency host guards

The separate `--fast-low-latency-guards` policy requires compact stock
execute and does not change the v9 artifact. It replaces the blind 50 ms
stock-to-fast wait with POSIX `tcdrain()`, so the baud change occurs only after
the adapter reports its transmit queue empty. The physically safe default
retains the 20 ms extension and stream turnaround guards and reduces only the
post-success guard from 20 to 10 ms. The latter still exceeds the roughly
7.8 ms wire time of all three 5-byte success frames; measured target drain then
completes before the host changes back to resident 8O1.

The fixed wait is reduced by 10 ms. For compact execute, its final
turn/execute/turn sequence has a roughly 24 ms wire floor, so replacing the
50 ms blind wait can save up to another 26 ms: **about 36 ms maximum**. Three
repeated clean v9 runs, the corruption/loss run, and the complete CP/M `DIR`
continuation pass in cosim with zero clean retries. Adding the full modeled
saving to v9's earlier estimate projects roughly **5.48 seconds**, but USB
queue overlap makes physical timing—not subtraction—the qualification gate.

The first CS00015 experiment used an explicitly shortened 5 ms extension
guard. It recovered and reached the prompt, and `DIR` worked, but the extension
and stream each retried once. The first disk request arrived at **10.167 s**
(stage 2.227 s, bulk 7.455 s), so 5 ms is rejected as a production default.
The exact run is preserved in
`evidence/juku-serial/cs00015-fastboot-v9-low-latency-20260815.json`.
Use `--fast-extension-guard-ms` only for named threshold experiments; the
default is 20 ms.

## Fast stages v10-v15: bounded decode, explicit readiness, buffered control

The later variants preserve v9 as immutable evidence and address two physical
races found by repeated CS00015 runs:

- **V10** replaces the fixed 256-byte producer-lead assumption with a bounded
  page-ahead input wait. This prevents the decoder from overtaking the ISR at
  different CPU/wire schedules. Its 5570-byte artifact has SHA-256
  `fff6f3d4b69eb2056b61a26ec1362b85bfe7a30f9d8e1938c97fa4acb330e1e2`.
- **V11** makes the one-record core acknowledge the `A5 3A` extension header.
  Two of four physical runs were retry-free, but two missed the first ACK. The
  host still sent all 610 remaining packet bytes after a missing ACK, so both
  runs contaminated the exchange and retried the extension and stream.
- **V12** makes the core sync search overlap-safe and sends only repeated
  `00 A5 3A` probes until the core answers `C5`; the extension body never
  precedes that answer. Four physical runs had zero extension retries. The
  fourth actually needed two probes and still continued cleanly, directly
  qualifying this repair. That run then exposed the independent fixed 2 ms
  `JZ`-to-stream race and retried the compressed stream once.
- **V13** applies the same contract to the stream. Its extension accepts
  overlap-safe `00 JZ` probes, initializes length, CRC, failure state, write
  pointer, saved stack, and interrupt reception, then answers raw `C6`. The
  host sends no compressed body before `C6`. The artifact is 5582 bytes
  (125/128-byte core, 620-byte extension, 4826-byte ZX0 payload) with SHA-256
  `7e4e5fcf821c6f16fd41349060650ad20361af4b8f1c77498fbf88488b6c38f9`.

The V13 regression deliberately delivers only a lone `A5` and lone `J` on the
first extension and stream probes. Both next probes resynchronize. Clean and
injected extension corruption, stream corruption, complete loss, lost reply,
3.4 MHz CPU stress, byte-exact B400h-CDFFh installation, prompt, and network
`DIR` all pass. V13 retains a modeled 296 ms gain over v7 and 23 ms over v8;
its 12-byte growth over v12 costs about 7 ms of 19,200-baud wire time.

Five subsequent physical V13 boots all reached CP/M, but only one completed
the first compressed stream without retry. The other four failed its CRC and
passed the complete retransmission, reaching the first disk request at
8.353-8.374 seconds instead of 5.769 seconds. Extension transfer itself was
clean in all five. The correlation was exact: every retrying run needed a
second extension-header probe, while the sole one-probe run was stream-clean.
Explicit state readiness fixed header ambiguity but did not eliminate the
phase-sensitive first-pass failure. The ideal USART/PIC cosim remains clean at
normal and 3.4 MHz schedules. A new one-shot timing fault delays one RxRDY IRQ
for over two character times after byte 900. That is sufficient to overrun V13,
produce exactly one stream retry, and then recover; V14 remains retry-free
under the identical disturbance because it polls the bulk receive path. This
does not prove the board's electrical root cause, but it reproduces the failure
class and distinguishes the two software architectures.

**V14** is the conservative control and current desk candidate. It keeps v13's
overlap-safe `A5 3A`/`C5` and `JZ`/`C6` contracts but returns to v7's fully
buffered path: receive all 4826 bytes at 4000h, verify CRC16/IBM, then decode
into B400h-CDFFh with interrupts out of the data path. The artifact is 5229
bytes: a 125/128-byte core, 267-byte exact extension, eight-byte `ZE`
descriptor, and unchanged payload. SHA-256 is
`83fd401af727a3c8c85fbe94d3d5458c71675efd974a0a8734f99987b420980c`.
Clean, partial-header, corrupted extension, corrupted/lost stream, lost reply,
one-shot RxRDY delay, 3.4 MHz, byte-exact handoff, prompt, and network `DIR`
simulations pass. It is
approximately v7 plus 11 high-speed bytes and explicit acknowledgements:
expected near 6.1 seconds, roughly 0.3 seconds slower than a clean v13 but much
faster than v13's observed retry path. This deliberately optimizes repeatable
latency rather than the best single run. Three physical CS00015 runs confirmed
that prediction at **6.115, 6.100, and 6.069 seconds**. Every extension and
stream completed without retry. Runs one and two needed a second extension
header probe, while run three needed only one; all stream headers needed one.
The overlap-safe handshake therefore recovered twice without contaminating the
body, and the complete first-request spread was only 46 ms.

The four V12 physical first-request times were 5.739, 5.740, 5.739, and
8.307 seconds. The last value includes one 2.56-second stream retry; the
extension remained clean. The best current repeatable physical result is thus
about 5.74 seconds, while v13's single clean 5.769-second run is not repeatable
enough for promotion. V14 is the current **physically qualified deterministic
candidate**. V12 retains the clean speed record, while v14 establishes the
repeatable physical baseline.

Decision: freeze V14 as the production fastboot baseline. Further variants
must address functionality, observability, or a reproduced reliability defect;
best-case millisecond savings alone do not justify reopening the timing path.

**V15** is such a functional variant, not another timing candidate. It keeps
V14's fully buffered, polling receive path and both explicit handshakes, but
loads CP/Mish's separately named 51K RAM BIOS at `B000h` and enters it at
`C600h`. The host recognizes the `JUKURM1` system container, validates its
declared length and CRC16/IBM, and extracts the exact resident bytes. The
6,249-byte artifact consists of a 125/128-byte core, 267-byte extension,
eight-byte `ZF` descriptor, and a 5,846-byte ZX0 stream expanding to 8,320
bytes. SHA-256 is
`3afd3f473bc9a18c6e0c8d4fa23c6ecdb015d21c5dd7c4fcb97c4d36492e2fb8`.

The first integrated simulation exposed a loader-stack collision: V14's
`B3F0h` stack lies inside V15's larger output range. The decompressor replaced
its own return addresses and escaped into `D85Dh`. V15 now keeps the loader
stack at `3FF0h`, immediately below the compressed input buffer. The focused
regression proves clean transfer, corruption and complete-stream-loss recovery,
the one-shot delayed-Rx case, byte-exact installation, cold prompt, RAM-matrix
`DIR`, 35 NetDisk-v2 reads, and a framebuffer independently rendered from the
captured transcript. Its final state is all-RAM mode 3 with PIC mask `FFh` and
no firmware service vectors installed. This is a simulator-qualified RAM-BIOS
experiment; V14 remains the hardware-qualified RomBios production baseline.
The stock-loader staging stub executes `DI` before copying this format: the
resident tail deliberately uses `CF00h..D07Fh`, including 128 bytes reclaimed
from the otherwise inactive RomBios workspace. Its builder rejects growth past
`D080h`; V15 is already interrupt-disabled and observes the same boundary.

The separately named CP/Mish `juku-fastboot-v15-netdisk-v3.bin` extends the
same RAM-owned design through `D5FFh`. Its 9,728-byte resident uses the former
RomBios workspace for a three-record cache, bounded NetDisk-v3 decoder,
receive-timeout state, and optional remote-console client; V14 and the original
V15/RAM-BIOS artifacts remain unchanged. Its 6,893-byte bundle contains a
6,490-byte ZX0 stream. Accordingly, only V15 accepts a
compressed payload below 8 KiB; V6-V14 retain the original below-6-KiB
validator. A protocol regression explicitly accepts the larger V15 bundle and
rejects the same size when labeled V14.

The end-to-end simulator path stock-loads the V15 core, installs the v3 image
byte-exact, stays in mode 3 with every IRQ masked, reaches CP/M, and completes
`DIR` in 12 host exchanges for at least 35 records. The matching server sends
up to three translated records per CRC16/IBM-protected response. It places a
4 ms guard between record descriptors because the 8080 may still be expanding
a fill record when the next wire byte would otherwise reach D11. The guard now
starts only after the server accounts for all bytes already queued at the
19,200/8O1 wire rate: `write()` completion is not physical UART completion.
With the old queue-time guard, the physical-time cosim reproduces D11's
one-byte-buffer overrun and the repeating CP/M disk error. A corrupt-first-CRC
injection produces exactly one duplicate request and then the same
framebuffer. Separate negotiation cases prove fallback to v2 compact and v1
raw replies, both with 35 requests.

NetDisk v3 operation `15h` is the CRC-protected synchronous write-through
counterpart to read-ahead `14h`. Its request carries the same 128-byte payload
as legacy write `12h`; its reply is `DJ`, sequence, status, zero record count,
and CRC-16/IBM. The resident client invalidates read-ahead before its first
attempt and uses the same three-attempt timeout/retry machinery as reads.
Legacy `12h` and its XOR reply remain unchanged for older clients.

The client also bounds every receive byte to 65,536 D11 status polls and every
transaction to three attempts. A disconnect therefore returns BIOS error 1
rather than trapping CP/M in an infinite poll; the next call starts a fresh
sequence. The end-to-end reconnect regression drops three complete replies
after the first prompt, observes CP/M's `Bad Sector` path, answers it, restores
host replies, and completes `TYPE README.TXT` without restarting the emulator.
Unlike a cache-warm `DIR`, that sequential read requires fresh host traffic.
The server's reply filter accepts an empty result specifically to model a
whole missing reply; altered non-empty replies must remain length-preserving.

`DIAG ALL` also exposed the tail of the RAM font overlapping the historical
`CE00h` CP/M directory buffer: both `|` glyphs changed into live `DIAG ` bytes.
V15 moves only its runtime directory/allocation/check buffers to
`D640h..D73Fh`, below the preserved `D773h` service slots and framebuffer.
Bytes above
the font's `7Dh` ceiling now render as `?`. The independent transcript renderer
checks the repaired final glyphs exactly; the older layouts are unchanged.

An explicit N4 marker adds the full remote-console baseline. Operation 20h
rate-limits remote key polling; operation 21h mirrors output after it is drawn
locally. A short receive deadline disables the remote side on host loss, while
local screen and matrix input continue; a later 256-status-call reprobe
reconnects it. Cosim types `VER` remotely and `DIR` locally, proves exact
remote/local/framebuffer transcripts and zero disk retries, then repeats with
the first console-poll reply dropped. The target disables, backs off, reprobes,
consumes the queued command, and completes without reboot. N3 remains the
default unless `--console-pty` is explicitly supplied.

### Direct-ROM V15 path (ekta4402)

The separately versioned `spinoffs/jukuravi/remix/ekta4402.bin` removes the
remaining stock bootstrap from the V15 path. Its monitor command `N` copies a
pinned 128-byte V15 core to `0100h`; that core immediately selects the proven
D57 mode-2/count-4 clock and D11 19200/8N1 framing. The host therefore starts
with the existing overlap-safe `A5 3A` extension handshake. There is no Janet
station discovery, 9600-baud record transfer, or stock execute service.

Build the CP/Mish artifacts, start this server, and press `N` alone (no Enter):

```sh
cd ~/fun/cpmish && make juku-fastboot-v15-netdisk-v3.bin \
    juku-net-v3-rambio-system.bin juku-net-v2.img && \
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v15-netdisk-v3.bin --direct-fastboot \
    --disk-baud 19200 --disk-protocol 3 --timeout 86400 \
    /dev/ttyUSB0 juku-net-v3-rambio-system.bin juku-net-v2.img
```

`--direct-fastboot` configures the initial host side as 19200/8N1, waits for
`N`, and excludes the operator wait from the reported transfer duration. The
result records zero stock frames/bytes. It is incompatible with
`--compact-stock-execute`, because there is no stock stage to compact. After
V15 enters its RAM BIOS, both ends use the normal 19200/8O1 NetDisk-v3 link.

Two independent regressions qualify the desk path. The ROM-level test loads a
checked synthetic extension and proves its execution. CP/Mish then boots the
real 6,893-byte bundle through `N`, reaches `A>`, and completes `DIR` in 12
disk exchanges. The latter also proves the 8N1-to-8O1 handoff. Ekta4402 has
not yet been burned or tested on physical hardware, so stock-ROM V14 and
ekta4401 remain the physical baselines.

The same direct-ROM transport is consumed by the separate
[`cpm-plus-juku`](https://github.com/ddanila/cpm-plus-juku) project. That
repository owns its CP/M Plus BIOS, system container, disk image, and
end-to-end `A>`/`DIR`/`DIAG CPU` regression; it imports this repository's
Ekta4402 ROM, simulator, and Janet host implementation. Keeping that boundary
prevents the genuine CP/M 3 port from becoming an artificial “CP/Mish 3”
variant while retaining one tested transport implementation.

Frame-level stock instrumentation also explains the 2.21/3.75-second stage
spread. A normal one-record request has 36 client frames after the request:
one request, 26 polls of other stations, one start poll, five ACKs, and three
advance polls. A slow run had 64. Those scans are owned by the stock ROM.
Sending the next fragment eagerly on every ACK was rejected in cosim: the ROM
discarded/rejected premature frames and host output grew from 14 to 44-58
frames. The captured Janet turn discipline remains unchanged.

Run the fastest current candidate without changing the ROM:

```sh
cd ~/fun/cpmish && make juku-fastboot-v14.bin
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v14.bin --compact-stock-execute \
    --fast-low-latency-guards --disk-baud 19200 \
    --boot-result-json cs00015-fastboot-v14-run1.json \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

`--boot-result-json` atomically records the stage hash, system hash, learned
station pair, individual stage/bulk timings, selected guard policy, and the
elapsed time from the first checksum-valid stock-ROM request to the first valid
resident disk request. It writes at that first request while continuing to
serve the disk, so a later interrupted session cannot lose the benchmark.
Use a distinct filename for every cold or warm run when collecting a timing
distribution.

Run the v8 comparison without changing the ROM:

```sh
cd ~/fun/cpmish && make juku-fastboot-v8.bin
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v8.bin --compact-stock-execute \
    --disk-baud 19200 \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

Run the physically qualified v7 path without changing the ROM:

```sh
cd ~/fun/cpmish && make juku-fastboot-v7.bin
../8080-cosim/tools/janet_disk_server.py \
    --fast-stage1 juku-fastboot-v7.bin --disk-baud 19200 \
    --writable --timeout 86400 /dev/ttyUSB0 \
    juku-net-mode2-system.bin cs00015-fastboot.img
```

Freeze the 2026-08-14/15 CS00015 comparison as six named physical baselines. All
used the same CP/Mish mode-2 system, host volume, cable, and machine. Timing
starts at the first checksum-valid Janet request and ends at the first valid
network A: request, so operator delay is excluded:

| CS00015 baseline | First disk request | Stock frames | Detail |
| --- | ---: | ---: | --- |
| **Fast stage v7** | timing not retained | 18 | prompt and `DIR` passed; 8N1 + ZX0; short handoff qualified |
| **Fast stage v6** | **6.214 s** | 18 | stage 2.21 s; bulk 3.53 s; zero retries; 8N1 + ZX0 |
| **Fast stage v5** | **6.551 s** | 18 | stage 2.23 s; bulk 3.84 s; zero retries; 8N1 bootstrap |
| **Fast stage v3** | **6.915 s** | 18 | stage 2.21 s; bulk 4.13 s; zero retries |
| **Fast stage v2** | **12.999 s** | 42 | stage 8.00 s; bulk 4.39 s; zero retries |
| **Fast stage v1** | **17.508 s** | 42 | stage 7.99 s; bulk 8.90 s; one recovered block-0 timeout |
| **Original stock 9600** | **73.873 s** | 330 | 6784 bytes / 53 records |

All seven runs reached the visible CP/M prompt. V5, v6, and v7 also completed a
physical `DIR` from network A:. V6 saved 0.337 seconds over v5 (**1.05x**,
5.1%) and 67.659 seconds over Original stock 9600 (**11.89x**, 91.6%). V5 saved 0.364 seconds over v3 (**1.06x**, 5.3%)
and 67.322 seconds over Original stock 9600 (**11.28x**, 91.1%). Fast stage
v3 saved 6.084 seconds over v2 (**1.88x**, 46.8%) and 66.958 seconds over Original stock 9600
(**10.68x**, 90.6%). Fast stage v2 saved 4.509
seconds over v1 (**1.35x**, 25.8%) and 60.874 seconds over Original stock 9600
(**5.68x**, 82.4%). Fast stage v1 remains frozen at its 4.22x/76.3% improvement
over stock. These values are retained as baselines; later stage, guard, window,
compression, or clock experiments must be recorded as separate variants rather
than replacing them. The raw
19200/8O1 wire floor for 6656 data bytes remains about 3.8 seconds. The
machine-readable record is
`docs/evidence/juku-serial/cs00015-fastboot-20260814.json`.

## Fast stage v2

V1's physical block-0 timeout has a deterministic software explanation. The
target repeats the critical header ACK three times, but the host treated the
first copy as line release and began block 0 while the target could still be
transmitting/draining the remaining copies. V2 waits 80 ms after header
acceptance before the ordinary 20 ms per-block guard. This costs 80 ms once and
removes the two-second reply timeout plus a 517-byte retransmission.

V2 also replaces the final bitwise CRC scan with cumulative per-block CRC
checkpoints. Exact instruction/data accounting for the frozen CP/Mish image
puts the removed scan at 4,297,085 8080 cycles: approximately 2.53 s at
CS00015's measured ~1.70 MHz (2.86 s at the conservative 1.5 MHz model). The
v1 binary remains byte-exact at 558 bytes and SHA-256
`b600758acf2bc10a068b003caf29d8799be6fa35489af6e23b8277360d334646`;
v2 is a separate 560-byte/five-record artifact.

Clean and corruption/loss/duplication/lost-ACK cosim runs pass for both
versions. The model projected approximately **12.8 s** from first Janet request
to first A: request on CS00015, derived from the frozen v1 timing by removing
its two-second timeout, one 517-byte retransmission, and 2.53-second scan, then
adding the one-time guard. The first physical run measured **12.999 s**, reached
the visible CP/M prompt, and completed all thirteen blocks with zero retries:
8.00 s for the stock stage and 4.39 s for the high-speed bulk phase. This close
agreement also validates the cycle-level explanation of v1's excess time.

Further worthwhile measurements are, in order:

1. repeat v14 on CS00014 and confirm zero retries, prompt, and `DIR`;
2. optionally extend the three clean CS00015 runs to ten cold/warm runs for
   long-term characterization, not as a promotion gate, recording
   stage, bulk, total, probes, retries, rejects, and Linux UART counters;
3. retain v12's 5.739-second clean result as the speed record, v13's five-run
   distribution as evidence, and v14's 6.069-6.115 s range as the deterministic
   physical baseline;
4. change the stock-ROM Janet turn discipline only if a new client-side design
   replaces it; eager host fragments are disproven;
5. keep production fastboot at 19,200. Revisit a higher rate only with new
   electrical evidence, because the in-spec x1 experiment already failed and
   count-2/x16 would exceed the USART clock limit by about two times.

## Post-v2 optimization study

The physical v2 split is dominated by the stock-loaded program, not the bulk
wire. Five stock records took 8.00 seconds while all 6656 high-speed bytes took
4.39 seconds. The v1/v2 and original-stock measurements imply approximately
1.37 seconds per additional 128-byte stock record and about 1.13 seconds of
fixed stock transaction cost. A one-record first stage therefore projects near
2.50 seconds and can save roughly 5.5 seconds before changing the bulk rate.

Fast stage v3 consequently uses a conventional two-stage shape: stock Janet
loads one 128-byte core at 9600; that core switches to the proven 19200/mode-2
clock and validates a compact extension loaded into low RAM; the extension
receives one continuous fixed-size system stream with a strong CRC. An error
retries the complete 6656-byte stream. This trades rare clean-cable
retransmission cost for eliminating twelve ordinary block turnarounds. It is a
separate experimental artifact; v1 and v2 remain byte-exact recovery choices.
Long packets and streaming are the established way to remove stop-and-wait
latency on a clean link, while shorter packets remain useful on noisy links;
the [Kermit protocol manual](https://www.kermitproject.org/protocol/kproto.pdf)
describes that exact tradeoff.

Do not weaken v3 to an additive checksum merely to keep its receiver fast. A
1983 [byte-wise CRC study](https://www.bitsavers.org/components/fairchild/_appNotes/Byte-wise_CRC_Jun83.pdf)
includes a 43-byte, table-free 8080 routine measured nearly four times faster
than its bit-at-a-time version. This is fast enough for the retained 19,200
stream and small enough for the high-speed extension. The one-record core
may use a compact Fletcher guard solely to authenticate that extension; the
resident system retains a polynomial CRC before execution.

The КР580ВВ51А limits rule out `mode 2 / count 3 / x16`: its roughly 410 kHz
USART clock exceeds the specified 310 kHz x16 maximum. The Soviet reference
gives x1 a 64 kHz clock ceiling, x16 a 310 kHz ceiling, and x64 a 615 kHz
ceiling; see the
[КР580ВВ51А reference tables](https://djvu.online/file/3bWMXUu35Lsw2).
The standards-respecting x1 path was subsequently tested by v4 at about
28,622.5 baud and failed its physical bidirectional negotiation. Production
fastboot therefore remains at the proven 19,200 mode-2/count-4 x16 setting;
higher baud requires new electrical evidence rather than another default
software variant.

Compression was cycle-benchmarked end to end before integration and audited
again after v7 fixed the 8N1 layout. Against the exact 6656-byte 2026-08-14
CP/Mish resident image, the comparison is:

| Encoding | Stream | Decoder | 8080 cycles | 8N1 stream + decode | Deployed delta from v7 ZX0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| none | 6656 | 0 | 0 | 3.467 s | +0.369 s |
| LZ4 raw, HC | 5821 | 94 | 424,565 | 3.282 s | +0.184 s |
| LZSA2 raw, ratio | 5129 | 277 benchmark | 795,228 | 3.139 s | +0.175 s |
| LZSA2 raw, speed | 5296 | 277 benchmark | 670,161 | 3.153 s | +0.188 s |
| ZX2 `-x` | 5054 | 74 | 950,249 | 3.191 s | +0.093 s |
| ZX1 | 5063 | 128 | 752,990 | 3.080 s | +0.049 s |
| **ZX0 classic** | **4826** | **92** | **993,353** | **3.098 s** | **baseline** |
| Exomizer P47T4 | 4756 | 285 | 2,511,481 | 3.954 s | +0.990 s |
| Exomizer P43 | 4756 | 258 | 3,347,152 | 4.446 s | +1.481 s |

Every measured decoder ran in the project's Intel 8080 instruction/cycle
model, produced all 6656 bytes at B400h-CDFFh byte-exactly, and uses
CS00015's measured 1.70 MHz CPU rate. Wire time uses v7's actual 19,200/8N1
ten-bit frames. The deployed delta also includes 128-byte extension padding:
v7 has 162 non-decoder bytes, so ZX1 needs one extra record and the benchmark
LZSA2 and Exomizer decoders need two. This corrects the earlier pre-v5 estimate
that used 8O1's eleven-bit framing and did not account for v7's nearly full
256-byte extension.

The [ZX0 compressor](https://github.com/einar-saukas/ZX0) uses classic `-c`
format with Ivan Gorodetsky's 92-byte v7 8080 decoder; the
[preserved source](https://emuverse.ru/wiki/%D0%92%D0%B5%D0%BA%D1%82%D0%BE%D1%80-06%D0%A6/%D0%A1%D0%B6%D0%B0%D1%82%D0%B8%D0%B5_%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85)
is attributed to Gorodetsky and Einar Saukas. ZX1 uses the corresponding
128-byte v5 decoder. ZX2 uses Einar Saukas's
[official compressor](https://github.com/einar-saukas/ZX2) and the surviving
[8080 v5 source mirror](https://github.com/parallelno/Vector06c/blob/master/Vector06c_Dev/_Projects/zx2/zx2.asm).
The [LZ4 decoder](https://github.com/michaelcmartin/bumbershoot/blob/master/asm/lz4core/lz4u_8080.asm)
is Michael C. Martin's 94-byte 8080 routine.
[Exomizer 3.1.2](https://bitbucket.org/magli143/exomizer/wiki/downloads/)
uses its official P43/P47T4 8080 decoders. LZSA2 uses the
[official 1.4.1 compressor and format](https://github.com/emmanuel-marty/lzsa);
its former external 8080 source repository is no longer available, so the
table explicitly labels a conservative format-derived benchmark decoder and
does not treat it as vendorable production code.

Even ignoring its larger decoder, ratio-mode LZSA2 loses 41 ms and speed mode
loses 55 ms to ZX0. A recovered or newly optimized LZSA2 decoder that still
costs one extra 128-byte record would have to finish below about **612,000
cycles** merely to tie v7; the conservative byte-exact implementation needs
795,228. ZX2's real decoder is 43,104 cycles faster than ZX0, but its 228 extra
wire bytes cost about 119 ms, leaving it 93 ms slower. LZ4's fast decoder
cannot repay 995 extra bytes. Exomizer compresses 70 bytes better but decodes
far too slowly. ZX1 wins about 18 ms before layout, then loses about 49 ms once
its extra extension record is transmitted. ZX0 therefore remains the fastest
measured and layout-valid choice, not merely the smallest-stream choice.

V9 also closes the remaining cheap preprocessing idea. Optimal ZX0 compresses
the exact resident image to 4826 bytes. Reversible 8080-aware normalization of
all CALL/JMP operands grows it to 5200 bytes; including absolute-memory
operands grows it to 5402, and including LXI operands to 5498. Even/odd byte
planes produce 5389, previous-byte XOR 5717, and previous-byte subtraction
5728 bytes. All would additionally require an inverse pass on the 8080. Raw
layout is therefore both the smallest stream and the lowest-decoder-overhead
choice among these transforms.

The separately named v6 implementation measured 0.701 seconds faster than v3
and 0.337 seconds faster than v5 on CS00015, with prompt and `DIR` proven. V7
keeps its codec while removing one extension record. V8 keeps the codec and
overlaps its receive/decode phases; its full modeled accounting is 273 ms
below v7 and awaits physical timing. V3 and v5 remain unchanged so the
compression and framing effects stay attributable.

Power-reset/restart during a long stream is now automated. The trace harness's
one-shot reset fault fires after byte 900 of V15, resets the CPU/USART and
memory view on the same PTY, and replays `TN`. The first host exchange times
out, returns the serial port to stock settings, accepts the ROM's new Janet
request, and completes a second byte-exact handoff. The disk-server CLI allows
three complete bootstrap rediscoveries by default (`--boot-restarts` changes
the bounded budget). This proves software recovery; physical reset behavior
still belongs in bench qualification.

The network-first V15 path also has a reset-with-stale-input fixture. It stops
the modeled target halfway through an extension body, starts a fresh target on
the same PTY, leaves the old partial bytes queued, and proves that overlapping
synchronization discards them before accepting a complete retransmission. The
CP/M Plus consumer adds malformed NetDisk-v3 cases: a truncated reply, 50 ms
reply guards, a duplicated full reply that deliberately raises modeled 8251
overruns, a bad CRC, and replacement by a fresh stateless disk server. All
recover without a target reset. Variable-sized `reply_filter` output exists
only to inject these deterministic test faults; the normal server still sends
complete protocol-sized frames.

A direct stock transfer to B400h was also tested as a possible zero-stage
shortcut. The stock client reached the requested CA00h execute address but did
not install the records at B400h (6327 of 6656 bytes differed in cosim). The
existing low-memory staging premise is therefore necessary; merely changing
the Janet record addresses is not a valid optimization.
