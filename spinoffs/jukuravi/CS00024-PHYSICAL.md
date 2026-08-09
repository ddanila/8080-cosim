# T31 physical session on CS00024

Date: 2026-08-08
Board: Arvutimuuseum Juku `CS00024`
ROM: exact T31 `1A/72EF`

## Retained result

Two cold boots decoded the exact T31 identity and repeated diagnostic bitmap
`18`: historical D55 and D57 bits. PIC, PPI and D54 passed. Compact RAM bitmap
`83` proved both `4000h..4FFFh` and `C000h..CFFFh` windows. Loader API v2
reached READY.

PROBE did not complete. With the corrected host retry path, three attempts
returned the same strong-parser-CRC error payload
`0006373F000000000034`. No RAM upload occurred. A later resident attach sent
three solicited RESYNC attempts but received no framed response.

Primary retained captures are:

- `sessions/cs00024-t31-initial/20260808T213309.146201Z.*`
- `sessions/cs00024-t31-default/20260808T213454.577423Z.*`
- `sessions/cs00024-t31-retryfix/20260808T213825.856067Z.*`
- `sessions/cs00024-t31-attach-resync/20260808T214255.525497Z.*`

The timeout-only retry capture at `20260808T213741.612920Z` is chronology, not
positive evidence.

## D55 supersession

The 2026-08-09 desk audit proves that exact T31 produces a D55 bit on a clean
clock-faithful structural board: all four D55 latch commands occur before the
new Mode-0 counts receive their required D54/D56 clocks. Therefore bitmap
`18` is valid evidence for a T31 D57-path failure but **not** evidence that
CS00024 D55, or even its complete functional path, is bad.

CS00024 currently has no valid D55 failure result. The next D55-specific board
action is a cold boot with clock-safe T34 `1C/A637`. Any T34 `08` must still be
interpreted as a path result covering D55, D9 select, local bus/strobes,
socket/power and D54/D56 clock sources. See
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).
