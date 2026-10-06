# Stock-ROM bootstrap and recovery

The production C host supports ordinary Janet boot and stock-assisted Fastboot.
For recoverable stock-ROM sessions, use **JF17 at 9,600/8O1 throughout**: Janet,
compressed transfer and NetDisk. The exact JF15 compatibility path remains
testable, but changes to 19,200/8N1 and cannot be selected with
`--recover-session`. Earlier experimental stage versions are historical.

## Supported paths

| Path | Transfer | Recovery boundary |
| --- | --- | --- |
| Ordinary stock Janet | Stock ROM's checked bootstrap records at 9,600/8O1 | Compatible system and NetDisk settings are required |
| Stock-assisted JF17 | One 128-byte core through Janet, Fletcher-checked extension and CRC-checked compressed system at 9,600/8O1 | Same C host can detect a checked stock request after target reset and boot again |
| Exact JF15 compatibility | Stock-loaded core, then 19,200/8N1 transfer | Frozen compatibility evidence; stock reset recovery requires JF17 |
| C8–C12 network ROM | Direct CRC-checked JF16 bootstrap under the chosen network-ROM profile | Separate network-ROM workflow; see the portable host contract |

The implementation is `host/src/jukuhost_runner.c` with the artifact/session
validation in `host/src/jukuhost_core.c`. The current Windows embedded stock
system and JF17 identities are in
[the payload manifest](../host/windows/payload-manifest.json).
The [portable host contract](portable-c-host-plan.md) owns platform qualification;
[the Windows guide](windows-jukuhost-client.md) describes GUI use.

## Operation

From this repository root, with the CP/M Plus project in its usual sibling
checkout, prepare the matching artifacts and native Linux host:

```sh
make -C ../cpm-plus-juku stock-recovery-check
sync/jukuhost_linux_build.sh
```

Provide a compatible CP/M Plus disk image, then use the appropriate serial
path for the connected board. Example:

```sh
build/jukuhost --serial /dev/ttyUSB0 \
  --system ../cpm-plus-juku/out/cpm-plus-juku-stock-recovery-system.bin \
  --fast-stage ../cpm-plus-juku/out/cpm-plus-juku-stock-recovery-fastboot-v17.bin \
  --volume ../cpm-plus-juku/out/cpm-plus-juku.img \
  --disk-protocol 3 --disk-baud 9600 --recover-session \
  --log /tmp/juku-stock.log --capture /tmp/juku-stock.cap
```

Select the stock ROM's network boot command on the target. Recovery does not
press keys or change the ROM's boot selection: the recorded CS00014 procedure
uses T → N after hardware reset. Passive discovery can also recognize a live
NetDisk request and attach to the already-running CP/M session.

The system, loader and CP/M handoff must agree on baud and PIT count. The
stock recovery system programs D57 count eight for 9,600 baud; count four in
the handoff would switch CP/M to 19,200 and leave NetDisk unavailable even if
JF17 transfer completed. Artifact guards check this boundary.

## Media and reset behavior

A: is read-only by default; B: remains read-only. CLI `--writable` enables
journaled A: writes. The [INI configuration](jukuhost-config.md) supports
`read-only`, `direct` and `snapshot`: snapshot uses a separate full working copy
of a hash-checked base image. Transaction replay and media identity checks
belong to the C host. A target reset does not substitute new media or authorize discarding changes.

## Verification and physical scope

| Evidence | Scope |
| --- | --- |
| `sync/jukuhost_core_check.sh` | Artifact framing, checksums, versions, serial profile and malformed-input rejection |
| `tests/jukuhost_stock_recovery_cosim_test.py` | Two complete JF17 boots with the same host process and target restart |
| `tests/jukuhost_stock_v15_cosim_test.py` and `tests/jukuhost_v15_delayed_pty_test.py` | Exact frozen JF15 compatibility and delayed-core handling |
| [CS00014 JF17 record](evidence/juku-serial/cs00014-stock-jf17-20260905/README.md) | Boot, operator-selected reset recovery and live host replacement at 9,600/8O1 |

The physical record binds the exact tested artifacts and captures; it does
not qualify later rebuilt system/loader pairs. It also does not qualify reset during an incomplete transfer, power cycling, disk writes or
broader diagnostics. PTY tests do not prove physical baud compatibility.
