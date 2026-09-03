# Windows Juku host client implementation status

This is the implementation and qualification ledger for
[windows-jukuhost-client-plan.md](windows-jukuhost-client-plan.md). A gate is
complete only when its implementation and named checks are present in the
repository. Physical results are never inferred from Wine, a simulator, or a
Linux USB adapter.

## W0 — product contract frozen

Status: **complete**

The first release is one 32-bit ANSI Win32 GUI executable named
`JUKUWIN.EXE`. It uses the existing C protocol/media core through a shared
runner, embeds all boot payloads, and leaves only its simple INI and disk
images as input files. The UI, configuration schema, deployment shape,
durability rules, non-goals, and test gates are frozen in the plan.

The embedded catalog is pinned by
[`host/windows/payload-manifest.json`](../host/windows/payload-manifest.json)
to `cpm-plus-juku` revision `1efbcd1` and these exact artifacts:

| Mode | Role | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| stock | system | 16,896 | `254f940e36501dcf3f46c5ba23b2b6cb3b1b7f3a13b1e42ae9786f2fa337a4a4` |
| stock | JF15 | 9,670 | `881befd8ebd306ae7313b2dff8b83cb8d964988e17627d76efedaa49e6a19a5d` |
| C11 | system | 18,432 | `923be9c41068b7de6f14d93dd7fd28e31bbefbf2fd68609c0483597092becd5f` |
| C11 | JF16 | 7,914 | `fc4fa48ef7c96064d7879782c293c740e30f73f50e06db2ad6fc09bbb0dd2d31` |

The stock pair is the exact JF15/system pair retained in
`tests/fixtures/jukuhost-v15` and physically accepted on CS00000. The C11 pair
is the exact system/JF16 pair from the accepted C11 manifest and the physical
CS00000 session.

The available USB adapter identifies as Prolific `067B:2303`, product
`USB-Serial Controller D`, and exposes no USB serial number. Consequently the
release contract uses a Windows device-instance identity when one exists but
must report ambiguity instead of guessing when two indistinguishable
adapters are attached. Its Windows driver identity and the qualification OS
version remain W4 evidence because no real Windows environment is currently
available.

The pre-extraction regression boundary is the existing strict core test,
Linux PTY integration, stock/JF15 co-simulation, C11 co-simulation, reconnect
test, and DOS build/emulator gate. W1 must keep all of those green.

## W1 — shared runner extraction

Status: **not started**

## W2 — Win32 platform and headless parity

Status: **not started**

## W3 — native UI and simple configuration

Status: **not started**

## W4 — physical current-Windows qualification

Status: **pending real Windows hardware and OS**

## W5 — physical legacy-Windows qualification

Status: **pending real Windows 95 hardware and OS**
