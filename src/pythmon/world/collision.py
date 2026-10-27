"""Grid-based collision rules for the overworld."""

from __future__ import annotations

from pythmon.world.tilemap import TileMap


def can_move_to(tile_map: TileMap, position: tuple[int, int]) -> bool:
    """Return whether the player may enter a target grid position."""
    return tile_map.is_walkable(position)
