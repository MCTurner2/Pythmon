"""Tile definitions and drawing for Pythmon maps."""

from __future__ import annotations

import pygame

from pythmon.world.map import GameMap


class TileDefinition:
    """Visual and gameplay properties for one map symbol."""

    def __init__(
        self,
        color: tuple[int, int, int],
        *,
        walkable: bool,
        border_color: tuple[int, int, int] | None = None,
    ) -> None:
        self.color = color
        self.walkable = walkable
        self.border_color = border_color


DEFAULT_TILES = {
    ".": TileDefinition((92, 164, 92), walkable=True),
    ",": TileDefinition((72, 142, 76), walkable=True),
    "#": TileDefinition(
        (54, 72, 58),
        walkable=False,
        border_color=(38, 48, 40),
    ),
    "~": TileDefinition(
        (60, 130, 190),
        walkable=False,
        border_color=(42, 96, 150),
    ),
}


class TileMap:
    """Render a ``GameMap`` and answer tile-level walkability queries."""

    def __init__(
        self,
        game_map: GameMap,
        tile_size: int = 48,
        tiles: dict[str, TileDefinition] | None = None,
    ) -> None:
        if tile_size <= 0:
            raise ValueError("tile_size must be greater than zero")
        self.map = game_map
        self.tile_size = tile_size
        self.tiles = dict(DEFAULT_TILES if tiles is None else tiles)

    def is_walkable(self, position: tuple[int, int]) -> bool:
        """Return whether a position is inside the map and can be entered."""
        x, y = position
        if not 0 <= x < self.map.width or not 0 <= y < self.map.height:
            return False
        symbol = self.map.tile_at(x, y)
        tile = self.tiles.get(symbol)
        if tile is None:
            raise ValueError(f"no tile definition for {symbol!r}")
        return tile.walkable

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Draw every map tile relative to the engine camera."""
        for y, row in enumerate(self.map.tile_rows):
            for x, symbol in enumerate(row):
                tile = self.tiles.get(symbol)
                if tile is None:
                    raise ValueError(f"no tile definition for {symbol!r}")
                rectangle = pygame.Rect(
                    round(x * self.tile_size - camera.x),
                    round(y * self.tile_size - camera.y),
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, tile.color, rectangle)
                if tile.border_color is not None:
                    pygame.draw.rect(surface, tile.border_color, rectangle, 2)
