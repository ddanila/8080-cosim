# EktaSoft remix ROM contract

`ekta4401` and its separately identified `ekta4402` successor are implemented
16 KiB derivatives of the pinned EktaSoft #0037 image. Their exact combined
and D15/D16 identities, builders and scoped physical qualification are in
[the remix guide](remix/README.md). They remain distinct from the archival
#0037 content used for faithful reconstruction.

## Implemented behavior

- Preserve the stock banner/console/monitor personality with an unmistakable
  remix identity. `H` lists commands and `V` runs a write-only diamond-tunnel
  framebuffer demo carrying `JUKU 2026`.
- `J` enters the Jukuravi transactional service monitor. It forces memory mode
  1, copies the T36 service segments from mapped ROM to their linked RAM
  addresses, initializes the 2400-baud serial path and takes exclusive control
  until RESET. This is not a returnable stock-monitor subroutine.
- The floppy subsystem is removed to provide service space. Its vectors retain
  explicit `NO DISK - NET ONLY` stubs; these images do not support floppy boot.
- Builders regenerate all eight stock verifier checksums across both ROM
  regions. The historical single-block diagnostic convention is insufficient.
- `ekta4402` adds direct `N fastboot`, copying its pinned V15 core to `0100h`
  and selecting 19,200/8N1 without stock Janet. This is the historical direct
  V15 path, not the current C8/C11/C12 JF16 network-ROM profile. Do not assume
  its artifacts can be substituted into that host configuration.

## Memory and programming boundaries

The in-place/relocated ROM split and the physical D15/D16 split are different.
Use the named low/high programming images and verify each chip; a combined
16 KiB file is not an 8 KiB programming image.

Service workspace and stack occupy RAM below `D800h`. `J` changes machine
state for its one-way session; the service and NetBios must not own the 8251
concurrently. The demo runs from copied low RAM with interrupts disabled while
mode 3 hides high ROM, then restores mode 1 before returning. Mode-1 framebuffer
reads see ROM, so the demo must remain write-only.

## Verification and remaining physical work

From the repository root:

```sh
python3 spinoffs/jukuravi/remix/build_ekta4401.py --check
python3 spinoffs/jukuravi/remix/build_ekta4402.py --check
sync/ekta4401_check.sh
```

These check exact images, checksum/command behavior and the applicable simulator
workloads. Physical service and direct-V15 observations are bound to their
recorded configurations in the remix guide; they do not qualify current host
platforms or every network-ROM profile.

The [normal-raster retention experiment](RASTER-REFRESH-EXPERIMENT.md) remains
prepared and unrun. T36 software-refresh success and normal video appearance do
not establish the hardware video-slot refresh schedule. Preserve that explicit
boundary until the staged physical control supplies evidence.
