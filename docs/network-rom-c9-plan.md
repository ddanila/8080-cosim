# JukuNet C9 contract and physical result

Status: **PHYSICALLY EVALUATED; CORE PATHS PASS, LOCAL VIDEO DEFECT FOUND;
NOT PROMOTED**.

C9 / ABI 1.4 is immutable. The named pair was evaluated on CS00000 on
2026-08-27: network boot, CP/M, N4, disk writes, diagnostics, warm boot,
recovery and host replacement passed. Local video remained blank despite
valid sync. A live EKTA-style `0Eh` PPI0 BSR write immediately restored video.
C9 is retained as physical evidence, not a promotion candidate. The separate
[C10 correction](network-rom-c10-plan.md) fixes POF release; the
[network-ROM overview](../spinoffs/jukuravi/network-rom/README.md) describes
later releases and their qualification scope.

## Implemented resident transport contract

These limits belong to the resident host-service routines in
`third_party/juku-common/platform/rom-host-services.asm`. They do not bound
the reset loader's accepted payload receive loop; see
[boot recovery limits](c11-session-recovery.md).

- Transmitter and receiver readiness are each bounded to 8,192 polls per
  byte. Reply-prefix acquisition has a 256-iteration scan budget; probing the
  second prefix byte can consume additional received bytes. The manifest
  currently labels the receive limit as 65,535 and the scan budget as bytes;
  those metadata fields do not describe the implementation limits.
- ABI 1.4 retains ABI 1.3's two-byte host-state prefix and appends negotiation
  flags and the failed operation, for four public state bytes. Failure reasons
  are `00h` none, `01h` TX timeout, `02h` RX timeout, `03h` synchronization
  budget, `04h` sequence, `05h` reply integrity and `06h` host status.
- Flag bits identify host detection, N4 selection, console capability,
  enabled mirroring and reconnection. The generated manifest owns their
  numeric assignments.
- N4 output is ordered and best effort. Failed remote output returns to local
  output; later input polling can reconnect without RESET. The physical POF
  defect above prevents claiming correct local pixels for C9.
- S21 bit 0 is reserved and boot is unconditional. Bits 2:1 retain the four
  video geometries; bits 4:3 retain the four character-bank policies.
- Earlier ABI vector addresses and calling conventions remain fixed. The
  `D600h..D7FFh` gate/work reservation and `0100h..9BFFh` TPA (39,680 bytes)
  are preserved, as are the 19,200-baud N3/N4 and NetDisk-v3 contracts.
- Disk writes remain synchronous. Persistent output buffers, new disk
  protocols, write-back caching and cryptographic boot authentication are
  outside C9. Runtime mode/bank selection is implemented separately in C12.

## Verification

| Evidence | Scope |
| --- | --- |
| `tests/network_first_rom_c9_test.py` | Finite return, failure reasons, malformed/silent/stuck transport, compatibility and S21 policy |
| `sync/network_first_rom_abi_check.sh` | C-model ABI, ROM identity, memory, local console and transport fixtures |
| `sync/network_first_rom_hdl_check.sh` | Default: structural reset/POST, ABI, POF and NetDisk DMA simulations. `--ci`: ROM-bench elaboration and POF simulation only; no physical display oracle |
| `sync/jukuhost_c8_cosim_check.sh` | Immutable native C8 production-host baseline without a CONOUT hook |
| `sync/jukuhost_c9_cosim_check.sh` | C9 production host, N4, CP/M disk/write/time/diagnostic/warm boot and host replacement |
| Sibling `cpm-plus-juku`: `make c9-check` | Matching CP/M system/TPA and local/remote integration |
| Sibling `cpm-plus-juku`: `make c9-simulator-candidate` | Reproducible non-physical package |

The fault test reports the largest cycle count observed across its success,
TX/RX timeout, truncated reply, prefix-budget, sequence, integrity and status
fixtures; this is not a bound over every possible transaction. It also checks
unconditional boot for all 32 S21 bit-4:0 combinations. The native-host C9 gate
uses production N4 output; the legacy C7 keyboard harness has a different
observation scope.

Run the C-model matrix from the repository root with Python 3 and a C compiler:

```sh
sync/network_first_rom_abi_check.sh
```

This also checks the other named ROM releases. The standalone C9 fault test
requires a compiled `cosim/trace.c` executable as its positional argument;
the shell gate builds that executable in temporary storage.

## Exact evaluated artifacts

Deterministic candidate identities are:

- combined ROM: `352417fafcf1ceaef40b8d39916acdaee6de03d914eafe2b54185ccbabe35530`;
- D15 low half: `b18e96e8f4cc88c7436e457b63b564ad42e1bf55f3e997f272301096c463593e`;
- D16 high half: `6f9bdf53bcf7ee919224305bcaf135c2d0076779218f49a2aed5395dc6baf932`;
- CP/M system: `ec06111e197a75a628d6a8c917542d0afa68c66ac26d14d39b9ef13aa0b38225`;
- Fastboot V16: `cae64165a04837d309f7b02c88a25754186ec333166ab5dd725d6e178088761b`;
- C9 full volume: `26f640ea6f0f7237910731f56ae006944d9102d51bfe5d217c4025a78d9fed10`;
  and
- non-physical candidate archive: `43b03802e156dba0492c860fe27a9fc1aec1672cf5dc0afab82176fbd243eb75`.

The per-release [ROM manifest](../spinoffs/jukuravi/network-rom/juku-network-rom-abi1.4-c9.json)
is the reproducible ROM/ABI authority. Its candidate-status text describes
the original simulator package. The physical qualification status is recorded
above; the sibling
[c9 physical worksheet](https://github.com/ddanila/cpm-plus-juku/blob/61b2d5397589e794c0381aa836b7a0da2217e6c8/docs/c9-physical-acceptance-worksheet.md)
records the named bench boundary. These identities and C9's physical defect
must remain distinct from subsequent programming candidates.
