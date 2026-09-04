# C12 runtime console and improvement ledger

Status: **ROM CORE AND HOST RECOVERY IMPLEMENTED; C-MODEL QUALIFIED; CP/M
CONSUMER, RELEASE PACKAGE, AND PHYSICAL ACCEPTANCE PENDING**

C12 is an additive successor to the immutable C11 ROM. It implements the one
fully specified, hardware-compatible improvement left in the retained design
record: switching video geometry and character bank at runtime without using
S21 or resetting the machine. It also gives the inherited passive boot beacon
a C12 identity so a host can report which ROM is waiting.

## ABI 1.5 contract

Feature bit `1000h` and vector `FF5Fh` identify `JCGCONCONFIG`:

| A | Operation | Inputs | Successful result |
| ---: | --- | --- | --- |
| 0 | query | none | A=reset-latched S21, B=active mode, C=active bank, D=override flags |
| 1 | set | B=mode 0..3, C=bank 0..3 | applies the complete pair, A=0/CY clear |
| 2 | default | none | reapplies S21 bits 4:1, A=0/CY clear |

Other selectors or a mode/bank outside 0..3 return A=`FFh` with carry set and
change neither state nor pixels. Override flag bit 0 means video differs from
S21; bit 1 means the character bank differs. The flags are independent.

A successful transition hides the old cursor, selects the new timing and font
policy, clears the complete 9,648-byte physical-raster envelope, resets cursor
position/blink, discards a pre-switch pending key, and publishes the active
pair before returning. Calls are synchronous under the existing
interrupt-disabled ROM ABI. Ordinary console initialization and CP/M warm boot
preserve the active override. Reset or an explicit `JCGINIT` restores the
latched S21 default.

The ABI 1.5 call-gate addition consumes exactly the five bytes that remained in
the fixed 224-byte `D620h` envelope. Active configuration and flags occupy
`D7FDh..D7FEh`, the only two-byte gap after the resident-host block; the
console state ending at `D7D9h`, per-drive NetDisk state at `D7DAh..D7DFh`,
host state at `D7E0h..D7FCh`, fixed `D600h..D7FFh` reservation, and CP/M TPA
remain unchanged.

## Boot discovery identity

C12 retains C11's passive, receive-only recovery behavior but emits checked
frame `4A 42 0C 01 05` (`JB`, C12, flags 1, XOR 5). C11 continues to emit its
byte-identical `JB/11` frame. The production host accepts both identities and
logs the received ROM generation; random or malformed data does not select a
boot path.

## Qualification and immutable boundary

`tests/network_first_rom_c12_test.py` proves:

- deterministic ABI 1.5 metadata, manifest, feature bit, `FF5Fh` vector, and
  exact 224-byte low-RAM gate;
- the immutable C11 combined SHA-256 remains
  `b93428bb33cd7e31c2d9b2b84aa07ea17edda76c9d53ab73b3cb8687e8d53dfd`;
- rejected selectors, mode values, and bank values do not publish partial
  state;
- all 16 runtime mode/bank pairs render against the independent font oracle,
  clear the physical raster tail, retain distinct defaults and active state,
  and survive ordinary console reinitialization.

The aggregate `sync/network_first_rom_abi_check.sh` retains every C4--C11
regression before running that C12 matrix. The deterministic simulator
artifacts are:

- combined: `7baa5943312fff869a0798197a6cd6a0f7961e93ee9c96509b73b20de3371aa4`;
- D15 low: `b95eb5b0842d501ee602d82a7907b1cf4baf3e1b2cd74f73ef553eac60faf9de`;
- D16 high: `c5e95491ba01da32f4b28be436d1261ae9d3fddf495b20bb2a15dca45ba404bb`.

These are not yet authorized as a burn pair. A matching CP/M consumer and
release manifest must be built and the focused visual/runtime switch matrix
must pass on CS00000 before physical promotion.

## Improvement disposition

Included in C12 because the contract and evidence are complete:

- atomic runtime video geometry and character-bank switching;
- separately observable S21 default, active pair, and override flags;
- warm-boot preservation and explicit default restoration;
- distinct `JB/12` discovery identity with C11-compatible host recovery;
- deterministic artifacts and exhaustive simulator regression.

Still required before calling C12 complete:

- a CP/M command for query/set/default and STATUS/diagnostic reporting;
- matching system/Fastboot artifacts, Windows-host C12 payload selection, and
  a deterministic release package;
- end-to-end native-host, structural HDL, Wine, and attended physical tests.

Not folded in without new evidence or a separate design decision:

- write-back disk caching, because power-loss semantics are unsafe;
- cryptographic boot authentication, because its 8080/EPROM/wire cost is not
  yet measured;
- higher serial rates, whose physical margin is unproved;
- RAM banking, which requires hardware support;
- XMODEM or host-side filesystem shortcuts that duplicate the authenticated
  bootstrap/NetDisk path;
- repurposing S21 bit 0 without a concrete distinct behavior.
