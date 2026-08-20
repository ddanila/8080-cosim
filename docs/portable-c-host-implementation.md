# Portable C host implementation status

This is the implementation ledger for the
[portable C host plan](portable-c-host-plan.md). It records admitted code and
evidence; unfinished items remain governed by the plan rather than being
silently narrowed.

## M0 — complete

Commit `81f64f76` froze the final Python-era production modules, five stock
systems, exact wire vectors, and required runtime behavior. The full baseline
passed all archived-system, station-learning, Fastboot, NetDisk, N4, media,
and reconnect regressions before implementation began.

## M1 — in progress

The first platform-neutral C99 slice is under `host/`:

- explicit Janet encoding and an incremental noise/checksum-resynchronizing
  parser;
- CRC-16/CCITT, CRC-16/IBM, Fletcher-16, and XOR primitives;
- checked Fastboot frames and strict V16 bundle metadata/payload validation;
- incremental N3/N4 request framing with bounded target-controlled lengths;
- ordinary and CRC-protected reply builders;
- V3 raw, fill, deleted-directory, and prefix/fill record encodings;
- 80-track and native 160-track geometry, bounds checks, read-only enforcement,
  and cylinder/head-interleaved `.JUK` conversion.

`sync/jukuhost_core_check.sh` compiles the same sources in strict C99 mode with
GCC using signed and unsigned `char`, with Clang when installed, and under
AddressSanitizer/UndefinedBehaviorSanitizer when supported. The C test reads
the same immutable `python-era-v1.txt` oracle as the Python contract test.

Still required before M1 closes:

- stock image recognition, staging bootstrap, and complete Janet boot state;
- the V16 transfer state machine, missed-ready recovery, and no-resend result;
- complete N3/N4 service semantics including duplicates and read-ahead;
- in-memory session/reconnect, logging/capture records, and media transaction
  recovery with fault injection;
- differential and malformed-input coverage for every admitted transition.

No platform backend or production command has been introduced yet. Python is
still the production host until M2 parity, caller migration, and retirement
all pass.
