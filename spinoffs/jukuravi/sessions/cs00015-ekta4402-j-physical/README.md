# CS00015 Ekta4402 `J` physical qualification

Date: 2026-08-16

Board: CS00015, fitted Ekta4402 D15/D16 pair. Serial link: Juku X3 through
the established RS-232 interface to `/dev/ttyUSB0`, 2400 baud, 8N1.

The operator booted the monitor and pressed `J` without Enter. The first host
capture (`20260816T195110.018407Z`) had already exhausted its wait before the
keypress: it contains zero received and transmitted bytes. Retain it as timing
chronology only; it says nothing about the ROM or board.

Two subsequent host processes attached to the already-resident loader without
RESET:

| Capture | Result |
| --- | --- |
| `20260816T195214.225806Z` | API v2 at `0A00h`; PROBE passed; refresh enabled for 128 rows from row 0 through API `07A9h`; zero transport mismatch |
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
PROBE and READ are non-destructive here; neither capture uploads or runs a RAM
snippet. The result directly qualifies Ekta4402's inherited `J` handler,
loader segment copy, serial/PIT restore, API-v2 negotiation, refresh service,
and bidirectional READ path on physical CS00015.
