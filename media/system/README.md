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

## PROM blocker status

The public archive pass that found `JUKUSYS.ZIP` also checked the museum software
ZIP listings for obvious Baltijets programming-disk payloads. It did not reveal
files corresponding to the small-PROM programs `ДГШ5.106.037`,
`ДГШ5.106.038`, `ДГШ5.106.039`, or `ДГШ5.106.092`. Those bytes still need the
referenced programming disk, physical PROM dumps, or an explicitly accepted
reconstruction.
