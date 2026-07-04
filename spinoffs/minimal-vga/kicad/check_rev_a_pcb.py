#!/usr/bin/env python3
import sys

import pcbnew


EXPECTED_COPPER_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
EXPECTED_ZONES = {
    "Rev A GND plane placeholder": ("In1.Cu", "GND"),
    "Rev A VCC plane placeholder": ("In2.Cu", "VCC"),
}


def fail(message):
    raise SystemExit(f"Rev A PCB check: FAIL: {message}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb"
    board = pcbnew.LoadBoard(path)
    copper_count = board.GetCopperLayerCount()
    if copper_count != len(EXPECTED_COPPER_LAYERS):
        fail(f"expected {len(EXPECTED_COPPER_LAYERS)} copper layers, found {copper_count}")

    names = {board.GetLayerName(layer_id) for layer_id in range(pcbnew.PCB_LAYER_ID_COUNT)}
    missing = [layer for layer in EXPECTED_COPPER_LAYERS if layer not in names]
    if missing:
        fail(f"missing copper layers: {', '.join(missing)}")

    footprint_count = sum(1 for _ in board.Footprints())
    if footprint_count < 80:
        fail(f"expected physical Rev A footprints, found only {footprint_count}")

    zones = {}
    for zone in board.Zones():
        layer = zone.GetLayer()
        zones[zone.GetZoneName()] = (
            board.GetLayerName(layer),
            zone.GetNetname(),
            zone.GetNumCorners(),
            zone.IsFilled(),
            zone.HasFilledPolysForLayer(layer),
        )
    for zone_name, (layer, net) in EXPECTED_ZONES.items():
        if zone_name not in zones:
            fail(f"missing zone: {zone_name}")
        actual_layer, actual_net, corner_count, is_filled, has_fill = zones[zone_name]
        if (actual_layer, actual_net) != (layer, net):
            fail(
                f"{zone_name} expected on {layer}/{net}, "
                f"found {actual_layer}/{actual_net}"
            )
        if corner_count < 4:
            fail(f"{zone_name} has incomplete outline ({corner_count} corners)")
        if not is_filled or not has_fill:
            fail(f"{zone_name} is not filled")

    print(
        "Rev A PCB check: PASS "
        f"({copper_count} copper layers: {', '.join(EXPECTED_COPPER_LAYERS)}, "
        f"{footprint_count} footprints, {board.GetNetCount()} nets, "
        f"{len(EXPECTED_ZONES)} power zones)"
    )


if __name__ == "__main__":
    main()
