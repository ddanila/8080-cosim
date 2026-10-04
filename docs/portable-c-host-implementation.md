# Portable Juku host implementation

The production implementation is `host/src/jukuhost_runner.c`, using the
portable protocol/media core and platform-specific serial, clock, console and
filesystem backends. `jukuhost_main.c` is the CLI adapter; `JUKUWIN.EXE` supplies
the Windows GUI. See [portable-c-host-plan.md](portable-c-host-plan.md) for the
runtime contract and remaining physical qualification.

## Implemented behavior

- Janet bootstrap with learned station identities and checked frames.
- Stock/JF17 reset-safe boot at 9,600/8O1; authenticated C8/C11/C12 Fastboot
  profiles, including bounded recovery when readiness markers are lost.
- N3 A:/B: disk service and N4 console, clock, report and capability traffic.
- Duplicate request suppression, snapshot media, transaction journaling,
  clean shutdown, serial reopen and target-reset recovery.
- Strict configuration, payload hashes, text logs and CRC-protected captures.
- File-backed media for the DOS conventional-memory boundary.

The runnable Python host is retired. Frozen non-runnable protocol fixtures
remain available to compare wire bytes and behavior.

## Capture conversion

`tools/jukuhost_evidence.py` checks capture framing and record CRCs, then
converts the host's request-event messages to JSON. It does not independently
decode or compare the captured RX/TX protocol frames. For example, from the
repository root:

```sh
python3 tools/jukuhost_evidence.py \
  docs/evidence/juku-serial/cs00000-ek37-c-host-v15-20260822T103131Z.cap \
  --requests-jsonl /tmp/jukuhost-requests.jsonl
```

Optional `--boot-result` output requires `--system` and `--fast-stage`. It
hashes those supplied files and derives completion from host events and the
first disk-request event; the caller must select the artifacts used in the
recorded run. Conversion alone does not prove their transmitted identity or
physical qualification.

The converter rejects truncated headers, incomplete records and bad record
CRCs before writing JSON. It does not salvage a complete prefix from an
interrupted capture. The C record decoder can decode earlier complete records
and returns `JH_NEED_MORE` for the incomplete tail.

When requesting both outputs, request JSONL is written before boot-result
validation. A failed conversion can therefore leave a new request file and
an older boot-result file; use the exit status before accepting either output
as evidence from that invocation.

## Verification entry points

| Area | Guard |
| --- | --- |
| Core vectors, malformed frames, media and journal faults | `sync/jukuhost_core_check.sh` |
| Runner API and cooperative cancellation | `sync/jukuhost_runner_check.sh` |
| POSIX integration, named PTY loss/reopen and retirement boundary | `sync/jukuhost_linux_check.sh` |
| C8 boot, missed-ready recovery, N4 and writable media | `sync/jukuhost_c8_cosim_check.sh` |
| C9 bounded transport and host replacement | `sync/jukuhost_c9_cosim_check.sh` |
| Stock target reset with the same host process | `tests/jukuhost_stock_recovery_cosim_test.py` |
| DOS reproducibility and serial emulator | `sync/jukuhost_dos_check.sh` |
| Windows payload/config/API/PE/package checks | `sync/jukuhost_win32_check.sh` |
| Windows executable stock/C11/C12 simulator sessions | `sync/jukuhost_win32_wine_e2e.sh` |

Physical evidence is linked from the platform qualification table in the
contract. Artifact identities belong in the relevant acceptance record or
package manifest rather than in this implementation overview.
