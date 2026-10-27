"""Data structures and loading helpers for Pythmon maps.

Maps are intentionally kept independent from rendering and game state.  The
current source format is a small ASCII file, but callers consume a
``GameMap`` so the source can later be replaced with JSON or Tiled data
without changing movement or rendering code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MapEntity:
    """An object placed on a map grid."""

    kind: str
    position: tuple[int, int]


@dataclass(frozen=True)
class GameMap:
    """A rectangular tile map and the entities placed on it."""

    tile_rows: tuple[str, ...]
    entities: tuple[MapEntity, ...] = ()

    def __post_init__(self) -> None:
        if not self.tile_rows:
            raise ValueError("map must contain at least one row")
        width = len(self.tile_rows[0])
        if width == 0:
            raise ValueError("map rows cannot be empty")
        if any(len(row) != width for row in self.tile_rows):
            raise ValueError("map rows must all have the same width")

    @property
    def width(self) -> int:
        """Return the map width in tiles."""
        return len(self.tile_rows[0])

    @property
    def height(self) -> int:
        """Return the map height in tiles."""
        return len(self.tile_rows)

    def tile_at(self, x: int, y: int) -> str:
        """Return the tile symbol at a grid position."""
        if not 0 <= x < self.width or not 0 <= y < self.height:
            raise IndexError("map position is outside the map")
        return self.tile_rows[y][x]

    @classmethod
    def from_ascii(cls, text: str) -> GameMap:
        """Parse an ASCII map, extracting entity markers from its tile grid."""
        rows = tuple(
            line.rstrip()
            for line in text.splitlines()
            if line.strip()
        )
        if not rows:
            raise ValueError("ASCII map does not contain any rows")

        entities: list[MapEntity] = []
        normalized_rows: list[str] = []
        entity_symbols = {
            "P": "player_spawn",
            "N": "npc",
            "H": "healing_station",
        }
        for y, row in enumerate(rows):
            normalized = list(row)
            for x, symbol in enumerate(normalized):
                kind = entity_symbols.get(symbol)
                if kind is not None:
                    entities.append(MapEntity(kind, (x, y)))
                    normalized[x] = "."
            normalized_rows.append("".join(normalized))
        return cls(tuple(normalized_rows), tuple(entities))

    @classmethod
    def from_file(cls, path: Path) -> GameMap:
        """Load an ASCII map from a UTF-8 text file."""
        return cls.from_ascii(path.read_text(encoding="utf-8"))
