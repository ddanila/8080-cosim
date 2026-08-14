# Juku system binaries

Vendored public CP/M and EKDOS system binaries from the Juku software archive.
These are preservation/reference artifacts for disk and system-software work;
they are not the missing РЕ3/РТ4 PROM programming payloads.

Source archive:

- `https://elektroonikamuuseum.ee/failid/juku/tarkvara/JUKUSYS.ZIP`

## Contents

| File | Size | Embedded string / role | SHA-1 | SHA-256 |
|---|---:|---|---|---|
| `CPM22.BIN` | 10240 | `CP/M 2.2` system binary | `2aebef05268e637b692f876403723350d8537d47` | `b9665d9af00f66bf51a5deda02fad3149b8fd3820c020e252d49f607362fee79` |
| `CPM231E.BIN` | 10240 | `52K CP/M 2.31e` system binary | `b68f81b5e14995549ec6664b335e9304dee986ba` | `230aa5952cd62596ac8a71bfd5addbb840a51ec51987d882fda958d2f9817939` |
| `EKDOS229.BIN` | 10240 | `52K EKDOS 2.29` system binary | `874c459df0072d871d281724f8c9e20ccf3eee2a` | `496473a0461e2c09546d0587fc83292e78e9e57e5ef19e1565ac3a602dc3677e` |
| `EKDOS230.BIN` | 10240 | `52K EKDOS 2.30` system binary | `a1134d27b358086d15133befef5a4a28d7304042` | `819d0ab7a30fbb8e87ebe42eddc2da599816f21b131f96bab2bd8f7cdc4f96d8` |
| `EKDOSVSW.BIN` | 10240 | EKDOS variant / switchable system binary | `8eaf8bba4a326ec5889db3d7b3e409a44ad783c8` | `8c70eda07c2cde8e73a0e664d7ff51356b4559649fad6df24f45784f3076e994` |

Verify with:

```sh
(cd media/system && sha256sum -c SHA256SUMS)
```

## Serial network boot

These 10 KiB files are SYSGEN/system-track images, not binaries that can be
jumped to at `0100h`. Bytes `0000h..01FFh` are four unused `E5`-filled sectors;
the runnable 52-sector system at `0200h..1BFFh` belongs at the source-defined
`CCP=B400h`, with cold BIOS entry `CA00h`. The remaining allocation tail is not
part of the runnable system (the isolated `FFh` in `EKDOSVSW.BIN` is likewise
outside the 52 sectors).

`tools/janet_netboot.py` recognizes this format and creates an in-memory 128-byte
8080 staging record. The stock NetBios loads the resulting 6,784-byte executable
at `0100h`; it copies the exact 6,656 system bytes to `B400h` and jumps `CA00h`.
No source image is modified.

```sh
# Configured physical Juku: start this, then type TN (no Enter).
# Use TN0201 only if NetBios prompts for maximum/own station numbers.
tools/janet_netboot.py /dev/ttyUSB0 media/system/EKDOS230.BIN

# Simulator proof for all five images.
sync/janet_netboot_check.sh
```

The proven stock setting is nominal 9600 baud, 8O1. The regression exercises
the real PTY serial/PIC/NetBios path and requires a byte-exact `B400h` image plus
the `CA00h` handoff; it does not inject RAM.

## PROM search result

The archive containing these system binaries has no obvious programming files
for PROMs `.037`, `.038`, `.039`, or `.092`. Validated physical dumps for all
four PROMs are now stored under `ref/physical-proms/`; the programming-disk
search remains useful only for provenance.
