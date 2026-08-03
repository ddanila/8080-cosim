#!/usr/bin/env python3
"""Emit the T30 monitor, which never depends on runtime TxEMPTY."""

from __future__ import annotations

from build_d2_loader_v2 import emit_loader as emit_loader_v2


ENTRY_PROGRESS_MARKER = 0xE3


def emit_loader(asm, **kwargs):
    return emit_loader_v2(
        asm,
        **kwargs,
        bounded_serial_put=True,
        entry_progress_marker=ENTRY_PROGRESS_MARKER,
        avoid_tx_empty=True,
    )
