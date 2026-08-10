# Jukuravi loader API v2

T28 introduced this API; T31/T34 retain its original capability set, T35
adds a compatible refresh command/capability, and T36 corrects its physical
row sweep. These names identify ROM
revisions, not different loader API versions.
The normal cycle is:

1. the host writes code and input data to RAM;
2. the host verifies the exact bytes with READ or CRC;
3. the ROM calls the selected entry point;
4. the snippet leaves its primary result in A and optional structured results
   in RAM, then executes an ordinary 8080 `RET`;
5. the ROM reports A, the host reads any result block, and the command monitor
   remains live for the next operation.

A board RESET is recovery for a non-cooperative or crashed snippet, not part of
normal command execution.

## Immutable memory and machine contract

| Range/address | Purpose |
|---|---|
| `0000..1FFF` | 8 KiB diagnostic/monitor ROM |
| `0A00` | `SERIAL_GET`: wait for a raw byte, return it in A |
| `0A03` | `SERIAL_PUT`: transmit A, then return |
| `0A06` | emergency loader re-entry; resets SP/transport and emits READY |
| `0A09` | `PRINT`: transmit the zero-terminated string at HL |
| `07A9` | T35/T36 `REFRESH`: preserve BC/DE/HL/SP; clobber A/flags |
| `4000..BFFF` | host LOAD/READ/CRC/RUN window |
| `C000..CFFF` | loader parser, state, scratch, and downward-growing stack |
| `D000` | loader stack top (first push writes below this address) |

Uploaded code must not write `C000..CFFF`. The entry values of registers are
unspecified. In CALL mode the loader pushes a ROM continuation before entering
the snippet. A cooperative snippet may use the stack normally but must make its
final `RET` reach that continuation. Only returned A is part of the register
ABI; use an agreed RAM block for every larger result.

After a cooperative `RET`, the ROM immediately saves A, executes `DI`, restores
SP to `D000`, and reinitializes the 8251 plus D57 channel 0 to the bootstrap
2400-baud configuration before emitting RETURN. Thus a snippet may temporarily
change the interrupt enable state, stack pointer, USART mode, or baud timer if
it still reaches the saved continuation. The loader test suite exercises all
four of those disturbances.

`JMP 0A06h` remains an emergency software escape for old/nonstandard payloads.
It abandons the payload stack and starts a fresh loader session, so it does not
preserve returned A and is not the normal completion mechanism.

## Transport envelope

The fixed Juku-side link is asynchronous 8N1 at approximately 2400 baud. The ROM
solicits every physical host-to-ROM symbol with alternating `C6`/`C7` request
tokens. A logical bit is represented by an odd, host-configurable number of
`55`/`AA` votes (`55` = 0, `AA` = 1). T28–T34 boot with seven votes; T35/T36 boot
with one to minimize the elapsed-time/parser exposure found on CS00024.
Invalid physical values are discarded without consuming a vote.

All logical records use:

```text
A5 5A TYPE LENGTH PAYLOAD... CRC8
```

CRC8 is CRC-8/ATM over TYPE, LENGTH, and PAYLOAD. Every host command additionally
ends its payload with CRC-16/CCITT-FALSE over TYPE, final LENGTH, transaction,
and command body. The ROM recomputes this CRC16 from its stored C000 parser
buffer, so a UART-valid frame cannot conceal a failed RAM store.

Host command payloads begin with an opaque one-byte transaction. Multi-byte
addresses, CRCs, and execution IDs are big-endian.

| Type | Command body after transaction and before CRC16 |
|---:|---|
| `23` PROBE | 0..16 opaque bytes, echoed exactly |
| `24` CONFIG | odd vote count in `1..15` |
| `25` LOAD | address, then 1..32 bytes |
| `26` READ | address, count in `1..32` |
| `27` CRC | address, count in `1..32` |
| `28` RUN | address, mode, 32-bit execution ID |
| `29` RESYNC | empty |
| `2A` REFRESH | operation: `00` query, `01` enable, `02` disable, `03` reset counter |

RUN mode `00` is CALL/RET. Mode `01` is a one-way `PCHL` for a resident monitor
or operating program that is not expected to return to the loader.

ROM responses are:

| Type | Payload |
|---:|---|
| `B0` RESULT | transaction, status, command, decoded length, address, count, data CRC16, parser-store retry count |
| `B1` DATA | transaction, status, command, address, count, exact data |
| `B2` RETURN | transaction, status, returned A |
| `A3` READY | API version/capabilities and immutable memory/transport limits |
| `AF` ERROR | outer-CRC status when no trustworthy transaction exists |

Status `00` is success. `01..08` mean outer CRC, unknown command, bad length,
bad range, verified store failure, stored-buffer CRC16 failure, bad config, and
workspace failure.

## Retry and reconnection rules

PROBE, CONFIG, LOAD, READ, CRC, RESYNC, and all REFRESH operations are
idempotent. The host retries a
complete command with the same transaction and independently verifies written
bytes. LOAD retries are safe because the same bytes target the same addresses.

RUN has a separate random 32-bit execution ID. The ROM caches the latest
invocation and its returned A. Repeating the exact address, mode, and execution
ID replays RESULT and RETURN without executing the snippet again. This makes a
damaged or lost acknowledgement/RETURN recoverable even for non-idempotent
snippets. A genuinely new invocation must use a new execution ID.

If the host disappears while the loader is receiving, eight bounded idle receive
periods discard the partial parser, restore that ROM's boot-vote default,
reset the stack, and return to frame sync. T35/T36 also invalidate the exact
disable signature, so recovery is refresh-on. A new host can attach without
RESET, issue RESYNC, inspect retained RAM, resume an interrupted upload, or call
already-resident code.

Examples from the repository root:

```sh
# Upload, verify, call, collect A and a 16-byte result block.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --load task.bin --load-address 4000 --run-address 4000 --run-mode call \
  --result-address 4100 --result-length 16

# Prepare a resident routine without invoking it.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --load task.bin --load-address 4000 --load-only

# In a later host process: attach, call retained code, read its result, no RESET.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --probe-loader --run-address 4000 --run-mode call \
  --result-address 4100 --result-length 16

# Attach only to inspect retained RAM.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --probe-loader --read-address 4100 --read-length 16

# T35/T36 attach: their resident bootstrap width is one vote.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --loader-bootstrap-votes 1 --probe-loader --loader-refresh query
```

The host defaults match the proven CS00015 path: a direct CP2102 -> MAX3232 ->
X3 connection at 2400 baud, one vote per logical bit, and a 6 ms response guard.
If another link is marginal, increase `--loader-guard-ms` first, then select an
odd majority with `--loader-votes 3`, `5`, or `7`. CRC-protected whole-command
retries remain enabled independently. A bridge whose USB side uses another
rate must set `--baud` explicitly.

That advice applies to an electrically marginal cable. It is the wrong
direction for a proven destructive elapsed-time/RAM boundary: warm CS00024
repeated CONFIG `strong_crc` at the 6 ms guard, while guard 0 completed the same
bootstrap and exact marker read. Minimize guard and vote count when shortening
the command is the experiment; do not describe that as improved signal
integrity.

`--loader-config-first` is the explicit T28–T34 CS00024 recovery policy. Those
loaders start at seven votes either way; the option sends the shorter CONFIG
frame first, switches both peers to the requested width, and only then sends
the exact-cookie PROBE. Normal PROBE-first ordering remains the default. This
policy is appropriate only when short seven-vote commands are proven but a
longer bootstrap command crosses a parser-retention/timing boundary. CONFIG is
idempotent, and the subsequent PROBE remains mandatory evidence rather than
being skipped.

T31 also permits transport benchmarking without a ROM rebuild. This example
configures the resident monitor once, then repeats a 29-byte idempotent LOAD and
an independent RAM CRC ten times. The default three bounded attempts remain
available for each command, while the JSON exposes every attempt and retry:

```sh
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --load spinoffs/jukuravi/firmware/return-4000.bin \
  --load-address 4000 --load-only \
  --loader-benchmark-passes 10 --no-loader-readback \
  --log-dir spinoffs/jukuravi/sessions/speed-v1-g6
```

`--loader-benchmark-passes` requires `--load-only`, rejects `--loader-resume`,
and does not execute the fixture. Each JSON pass records LOAD and verification
attempts and elapsed time. The aggregate records retry counts, parser-buffer
store retries, verified payload bytes, and effective LOAD-plus-CRC payload
rate. Use `--loader-retries 1` when measuring strictly one command attempt;
larger values measure the intended host-controlled whole-command recovery
policy.

## Last-frontier RESET cases

No ROM monitor can regain execution while the 8080 is stuck in arbitrary code.
A hardware RESET remains necessary when a snippet loops forever, executes HLT
without a usable interrupt, loses/corrupts its return continuation, overwrites
the reserved loader workspace, or otherwise never reaches the ROM. Those are
explicit crash cases. Transport loss, a restarted host, a partial upload,
corrupt commands, failed RAM stores, lost responses, and completed snippets do
not normally require RESET.

CS00024 adds one hardware-specific exception: an unrefreshed mutable loader
workspace can decay while the ROM remains alive enough to emit transport
requests. Reattach then cannot reconstruct corrupt `C000h` state. Its exact
same-process retention evidence and refresh-capable successor-ROM requirement
are in [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md).

## T35/T36 refresh extension

T35 and T36 advertise capability bit `4000h`, total capabilities `7FFFh`, boot votes
`01`, and command `2Ah`. Its nine DATA bytes are: extension version, effective
enabled flag, policy flags, row start, row count, public API high/low, and
16-bit receive-poll refresh-call counter high/low. Version is `01`; policy flags are `07`; row
geometry is start `40h`, count `80h` on historical T35 and start `00h`, count
`80h` on T36; the public call is `07A9h`. Row start describes the CPU address
sweep; it does not mean T35's high byte reached physical DRAM row inputs.

The T36 enabled call reads all 128 MK4564/К565РУ5 physical refresh rows in
2,115 nominal T-states (1.2339 ms at CS00024's measured 1.714065 MHz effective
RAM-loop rate). T35 has the same timing but increments CPU H and therefore
repeats physical row zero. T35/T36 invoke it in
blocking RX/Tx waits and its Tx-drain delay. A long uploaded CALL-mode snippet
must start consecutive `CALL 07A9h` sweeps no more than 2 ms apart. At the
measured CS00024 rate this leaves about 0.7 ms of non-refresh work between the
1.2339 ms calls. Arbitrary RUN code is not preempted and cannot be made safe by
host configuration.

Refresh is fail-safe. Only exact RAM signature `5A A5 3C` disables it; every
other value enables it. RESYNC, idle reset, and transport recovery invalidate
the signature. `--loader-refresh auto` (the host default) queries the refresh-capable ROM and
repairs an unexpected disabled state. `disable` is intentionally available for
retention experiments, may make the loader unrecoverable until hardware RESET,
and must never be treated as a normal operating mode. The host verifies the
reported transition and rejects a torn disable.
