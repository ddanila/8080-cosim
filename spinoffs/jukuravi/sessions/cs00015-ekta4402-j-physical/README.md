# CS00015 Ekta4402 `J` physical qualification

Date: 2026-08-16

Board: CS00015, fitted Ekta4402 D15/D16 pair. Serial link: Juku X3 through
the established RS-232 interface to `/dev/ttyUSB0`, 2400 baud, 8N1.

After entering the loader with `J` without Enter, two host processes attached
without RESET. The empty capture `20260816T195110.018407Z` provides no board or
ROM evidence.

| Capture | Result |
| --- | --- |
| `20260816T195214.225806Z` | API v2 at `0A00h`; PROBE passed; refresh query reported enabled for 128 rows from row 0 through API `07A9h`; zero transport mismatch |
| `20260816T195246.333501Z` | Repeated the preceding checks and completed a single-attempt 32-byte READ at `4000h`; zero transport mismatch |

The successful control command was:

```sh
python3 spinoffs/jukuravi/host.py \
  --port /dev/ttyUSB0 --baud 2400 \
  --attach-loader --probe-loader --loader-bootstrap-votes 1 \
  --loader-refresh query --loader-timeout 30 --timeout 10 \
  --log-dir spinoffs/jukuravi/sessions/cs00015-ekta4402-j-physical
```

The second command additionally used `--read-address 4000 --read-length 32`.
Neither capture uploads or runs a RAM snippet. PROBE and READ use the
reserved loader workspace; they do not overwrite the requested data range.
The result directly qualifies Ekta4402's inherited `J` handler,
loader segment copy, serial/PIT restore, API-v2 negotiation, refresh service,
and bidirectional READ path on physical CS00015.
