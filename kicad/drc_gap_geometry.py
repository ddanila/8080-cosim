#!/usr/bin/env python3
"""Resolve KiCad DRC item markers to routable copper coordinates."""

from __future__ import annotations

import math

import pcbnew


def board_item_points(
    board: pcbnew.BOARD,
) -> dict[str, tuple[tuple[float, float], ...]]:
    """Return useful connection points for DRC-addressable copper items."""
    result: dict[str, tuple[tuple[float, float], ...]] = {}
    for item in board.GetTracks():
        start, end = item.GetStart(), item.GetEnd()
        result[item.m_Uuid.AsString()] = (
            (pcbnew.ToMM(start.x), pcbnew.ToMM(start.y)),
            (pcbnew.ToMM(end.x), pcbnew.ToMM(end.y)),
        )
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            position = pad.GetPosition()
            result[pad.m_Uuid.AsString()] = (
                (pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)),
            )
    return result


def resolved_item_pair(
    left: dict,
    right: dict,
    points_by_uuid: dict[str, tuple[tuple[float, float], ...]] | None,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Resolve a DRC pair to its nearest actual endpoints, with marker fallback.

    KiCad reports a track's ``pos`` at its midpoint.  That is useful for the DRC
    UI but is not the open end that a repair route must join.
    """
    fallback_left = ((float(left["pos"]["x"]), float(left["pos"]["y"])),)
    fallback_right = ((float(right["pos"]["x"]), float(right["pos"]["y"])),)
    if points_by_uuid is None:
        left_points, right_points = fallback_left, fallback_right
    else:
        left_points = points_by_uuid.get(str(left.get("uuid", "")), fallback_left)
        right_points = points_by_uuid.get(str(right.get("uuid", "")), fallback_right)
    return min(
        ((a, b) for a in left_points for b in right_points),
        key=lambda pair: math.dist(pair[0], pair[1]),
    )
