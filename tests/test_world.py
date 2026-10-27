"""Automated tests for map content and overworld encounter behavior."""

import unittest

import pygame

from pythmon.world.map import GameMap
from pythmon.world.tilemap import TileMap
from pythmon.states.overworld import OverworldState


class InputStub:
    def __init__(self, *keys: int) -> None:
        self.keys = set(keys)

    def is_key_pressed(self, key: int) -> bool:
        return key in self.keys


class WorldTests(unittest.TestCase):
    def test_map_extracts_healing_station_and_grass_is_walkable(self) -> None:
        game_map = GameMap.from_ascii("#####\n#PH,#\n#####")
        self.assertIn(
            ("healing_station", (2, 1)),
            {(entity.kind, entity.position) for entity in game_map.entities},
        )
        tile_map = TileMap(game_map)
        self.assertTrue(tile_map.is_walkable((2, 1)))

    def test_entering_grass_can_start_a_wild_battle(self) -> None:
        state = OverworldState(InputStub(pygame.K_RIGHT), encounter_roll=lambda: 0.0)
        started: list[bool] = []
        state.start_battle = started.append
        state.player_position.update((18, 7))
        state.update(0.0)
        self.assertEqual(started, [True])


if __name__ == "__main__":
    unittest.main()
