"""Tile-based overworld state."""

from __future__ import annotations

from importlib.resources import files
from collections.abc import Callable
import random

import pygame

from pythmon.world.collision import can_move_to
from pythmon.world.map import GameMap, MapEntity
from pythmon.world.npc import NPC_DIALOGUE, npc_at
from pythmon.world.tilemap import TileMap
from pythmon.states.dialogue import DialogueBox


class OverworldState:
    """Grid-based overworld state backed by an editable map asset."""

    TILE_SIZE = 48

    def __init__(
        self,
        input_handler: object,
        *,
        encounter_roll: Callable[[], float] | None = None,
    ) -> None:
        self.input = input_handler
        map_path = files("pythmon.data").joinpath("maps/starter_town.txt")
        self.game_map = GameMap.from_ascii(map_path.read_text(encoding="utf-8"))
        self.tile_map = TileMap(self.game_map, self.TILE_SIZE)
        spawn = next(
            (
                entity.position
                for entity in self.game_map.entities
                if entity.kind == "player_spawn"
            ),
            None,
        )
        if spawn is None:
            raise ValueError("map must define a player spawn with 'P'")
        self.player_position = pygame.Vector2(spawn)
        self.facing = (0, 1)
        self.dialogue: DialogueBox | None = None
        self.start_battle: Callable[[bool], None] | None = None
        self.open_menu: Callable[[], None] | None = None
        self.heal_party: Callable[[], None] | None = None
        self.encounter_roll = encounter_roll or random.random
        self.wild_encounter_chance = 0.2

    def update(self, _delta_time: float) -> None:
        """Handle dialogue, interaction, and one-tile movement."""
        del _delta_time
        if self.dialogue is not None:
            if self.input.is_key_pressed(pygame.K_e) or self.input.is_key_pressed(
                pygame.K_SPACE
            ):
                self.dialogue.advance()
                if self.dialogue.finished:
                    self.dialogue = None
            return

        if self.input.is_key_pressed(pygame.K_ESCAPE):
            if self.open_menu is not None:
                self.open_menu()
            return

        if self.input.is_key_pressed(pygame.K_b):
            target = (
                int(self.player_position.x) + self.facing[0],
                int(self.player_position.y) + self.facing[1],
            )
            if npc_at(self.game_map, target) is not None and self.start_battle:
                self.start_battle(False)
            return

        if self.input.is_key_pressed(pygame.K_e) or self.input.is_key_pressed(
            pygame.K_SPACE
        ):
            target = (
                int(self.player_position.x) + self.facing[0],
                int(self.player_position.y) + self.facing[1],
            )
            if npc_at(self.game_map, target) is not None:
                self.dialogue = DialogueBox(NPC_DIALOGUE)
            elif self._entity_at(target, "healing_station") is not None:
                if self.heal_party is not None:
                    self.heal_party()
                self.dialogue = DialogueBox(
                    (
                        "The Recovery Hub restores your party and move uses.",
                        "Your team is ready for the route ahead!",
                    )
                )
            return

        directions = (
            (pygame.K_UP, (0, -1)),
            (pygame.K_DOWN, (0, 1)),
            (pygame.K_LEFT, (-1, 0)),
            (pygame.K_RIGHT, (1, 0)),
        )
        for key, (x_delta, y_delta) in directions:
            if not self.input.is_key_pressed(key):
                continue
            self.facing = (x_delta, y_delta)
            target = (
                int(self.player_position.x) + x_delta,
                int(self.player_position.y) + y_delta,
            )
            if self._can_enter(target):
                self.player_position.update(target)
                if (
                    self.game_map.tile_at(*target) == ","
                    and self.encounter_roll() < self.wild_encounter_chance
                    and self.start_battle is not None
                ):
                    self.start_battle(True)
            break

    def _can_enter(self, position: tuple[int, int]) -> bool:
        """Return whether a tile is open and not occupied by an NPC."""
        return can_move_to(self.tile_map, position) and npc_at(
            self.game_map, position
        ) is None

    def _entity_at(
        self,
        position: tuple[int, int],
        kind: str,
    ) -> MapEntity | None:
        """Return a map entity of the requested kind at a position."""
        return next(
            (
                entity
                for entity in self.game_map.entities
                if entity.kind == kind and entity.position == position
            ),
            None,
        )

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Draw the tile map and the player."""
        self.tile_map.draw(surface, camera)

        player = pygame.Rect(
            round(self.player_position.x * self.TILE_SIZE - camera.x + 8),
            round(self.player_position.y * self.TILE_SIZE - camera.y + 8),
            self.TILE_SIZE - 16,
            self.TILE_SIZE - 16,
        )
        pygame.draw.rect(surface, (52, 72, 196), player, border_radius=8)

        for entity in self.game_map.entities:
            if entity.kind == "npc":
                color = (196, 72, 52)
                inset = 12
            elif entity.kind == "healing_station":
                color = (220, 190, 64)
                inset = 8
            else:
                continue
            npc = pygame.Rect(
                round(entity.position[0] * self.TILE_SIZE - camera.x + inset),
                round(entity.position[1] * self.TILE_SIZE - camera.y + inset),
                self.TILE_SIZE - inset * 2,
                self.TILE_SIZE - inset * 2,
            )
            pygame.draw.rect(surface, color, npc, border_radius=6)

        if self.dialogue is not None:
            self.dialogue.draw(surface)
