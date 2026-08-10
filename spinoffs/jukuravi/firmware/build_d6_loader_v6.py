#!/usr/bin/env python3
"""Emit T35's low-4K loader core with cooperative DRAM refresh."""

from __future__ import annotations

from build_d2_loader_v2 import emit_loader as emit_loader_v2

import protocol

REFRESH_MODE = protocol.LOADER_V2_WORKSPACE_BASE + 0x128
REFRESH_COUNTER = protocol.LOADER_V2_WORKSPACE_BASE + 0x12C


def emit_loader(asm, **kwargs):
    return emit_loader_v2(
        asm,
        **kwargs,
        bounded_serial_put=True,
        compact_bounded_serial_put=True,
        entry_progress_marker=None,
        avoid_tx_empty=True,
        boot_votes=protocol.LOADER_V2_T35_BOOT_VOTES,
        capabilities=protocol.LOADER_V2_T35_CAPABILITIES,
        refresh_label="t35_refresh",
        refresh_mode_address=REFRESH_MODE,
        refresh_counter_address=REFRESH_COUNTER,
        external_fixed_frames=True,
        extra_dispatch=((protocol.TYPE_LOADER_V2_REFRESH, "t35_refresh_command"),),
    )
