#!/usr/bin/env python3
"""Emit the compact T31 loader entirely below ROM address 1000h."""

from __future__ import annotations

from build_d2_loader_v2 import emit_loader as emit_loader_v2


def emit_loader(asm, **kwargs):
    return emit_loader_v2(
        asm,
        **kwargs,
        bounded_serial_put=True,
        compact_bounded_serial_put=True,
        entry_progress_marker=None,
        avoid_tx_empty=True,
    )
