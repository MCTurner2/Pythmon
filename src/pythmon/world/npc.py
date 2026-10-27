"""Non-player character lookup and dialogue content."""

from __future__ import annotations

from pythmon.world.map import GameMap, MapEntity


NPC_DIALOGUE = (
    "Welcome to Pythmon! I am Professor Stack.",
    "In this world, wild programs roam beyond the town.",
)


def npc_at(game_map: GameMap, position: tuple[int, int]) -> MapEntity | None:
    """Return the NPC at a position, if one exists."""
    return next(
        (
            entity
            for entity in game_map.entities
            if entity.kind == "npc" and entity.position == position
        ),
        None,
    )
