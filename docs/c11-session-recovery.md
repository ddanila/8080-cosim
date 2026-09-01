# C11 boot and NetDisk session recovery

Status: **IMPLEMENTED AND CO-SIM QUALIFIED; PHYSICAL C11 ACCEPTANCE PENDING**

C11 is the first JukuNet ROM whose reset loader can be distinguished from an
already-running CP/M system without sending a probe from the host. This matters
because CP/M may be running a music player with interrupts disabled and may
legitimately emit no NetDisk request for minutes. A host start must not disturb
that program merely to discover its state.

## Wire contract

While its overlap-safe `JZ` scanner is idle, C11 periodically does this:

1. wait until the 8251 transmitter is empty;
2. select 19,200/8O1 and transmit two checked discovery frames
   `4A 42 0B 01 02` (`JB`, C11, flags 1, XOR 0);
3. wait for both copies to drain;
4. restore 19,200/8N1, emit the existing checked `JR16` marker, and resume the
   overlap-safe `JZ` scanner;
5. repeat after roughly one second of scanner inactivity at 1.7 MHz.

Only the idle `J`/`Z` scanner has a timeout. Once `JZ` is accepted, the length,
compressed body, CRC, decompression, and success handoff retain the existing
blocking/authenticated behavior. A slow but live payload is therefore never
decoded partially. C6 through C10 retain their exact 361-byte loader; the
C11-only loader is 456 bytes and occupies unused boot-only ROM at file offset
`0600h`.

The production host's `--recover-session` mode opens at 19,200/8O1 and remains
receive-only during discovery. A valid `JB/11` frame selects V16 at 8N1. A
complete checked `JD` request selects NetDisk at 8O1; the host puts that first
request back byte-for-byte before starting the ordinary service. Random `J` or
`JD`-like data is insufficient. During NetDisk, a valid boundary-aligned
`JB/11` frame is an explicit target-reset indication and returns the host to
V16.

## Recovery matrix

| Starting/failure state | ROM behavior | Host behavior | Result |
| --- | --- | --- | --- |
| target off or absent | no bytes | waits passively; logs every 5 s | no corruption; boot begins when C11 appears |
| C11 loader already waiting | repeats checked 8O1 beacon, then waits at 8N1 | detects beacon, selects 8N1, probes `JZ` | late host boots without RESET |
| CP/M already in NetDisk | retries checked `JD` requests | validates and preserves first request | attaches without `--resume-disk` |
| CP/M running silent music | emits no traffic | sends no discovery or ready bytes | program is left undisturbed until NetDisk resumes |
| board reset during NetDisk | C11 POST then checked beacon | closes NetDisk service state and restarts V16 | complete automatic reboot |
| reset during V16 | fresh C11 beacon/`JR16` | abandons partial stream and rediscovers | full authenticated retransmission |
| corrupt/truncated V16 body | CRC failure returns loader to discovery loop | sees a later beacon and retries complete V16 | no partial image executed |
| host process replaced | resident ROM times out and retries the request | replacement validates `JD` and serves it | no manual resume flag |
| named serial device disappears | target continues bounded request retries or C11 discovery | host retries reopen in bounded configured windows, then rediscovers | recovers when the device path returns |
| configured console PTY is absent or replaced | target continues bounded N4 retries | host waits for the endpoint before boot, or reopens it and rediscovers after loss | no successful boot is abandoned for a missing relay |
| capture/log/media/artifact failure | no safe ROM remedy | host stops with its specific fatal exit | unsafe or unaudited state is not hidden |
| permanent power, cable, UART, RAM, or ROM fault | may remain silent or repeat POST failure | waits/retries only where transport remains observable | operator/hardware repair is still required |

This is intentionally not claimed for the stock ROM: its boot and NetDisk
framing use different rates, and it cannot emit the C11 discovery contract.
The ordinary immediate `--network-rom` and explicit `--resume-disk` modes remain
available for C8-C10 and stock-era workflows.

## Qualification

`sync/jukuhost_c11_cosim_check.sh` retains an ordinary immediate-host C11 run
for backward compatibility and adds:

- passive C11 cold discovery;
- a late-host interval proving the beacon repeats;
- host replacement where the second host is not told CP/M is already alive;
- a board reset on the first host-to-target byte after the exact 7,784-byte V16
  exchange, proving NetDisk-to-beacon-to-V16 recovery;
- the complete DIR, STATUS, diagnostics, A:/B:, write/erase, time, and warm-boot
  workload after recovery.

The forced NetDisk-reset run completed with one target reset, one bootstrap
restart, zero service retries, and clean writable-journal behavior.

## C11 candidate supersession

This recovery work was explicitly folded into C11 before its physical ROM pair
was programmed. The earlier desk-only C11 candidate is retained in Git history
but is superseded and must not be burned:

- old combined: `49af4137be8cab2a487ccec0ac264e964b75f6699ebea8baf0f1a29d1ce292dc`;
- old D15: `4040833d71fe9029d9cf5bc261b76b57edb87528d1d624e6b003fb2208bf2187`;
- old D16: `ac80ca047adeff842a911266ff1c054e30ac4628e925ea9fbb1be54e872b9581`.

The recovery C11 pair is:

- combined: `b93428bb33cd7e31c2d9b2b84aa07ea17edda76c9d53ab73b3cb8687e8d53dfd`;
- D15: `a94e8fa2911fd3f7e715c6086d237b45fe630e71e8e14786bdcce435d99a8134`;
- D16: `ac80ca047adeff842a911266ff1c054e30ac4628e925ea9fbb1be54e872b9581`.

D16 is unchanged because the discovery loader lives in the lower D15 half.
Physical programming and the raster/listening acceptance remain separate
operator gates.
