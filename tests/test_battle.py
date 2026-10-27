"""Automated tests for battle rules and battle creation."""

import unittest

from pythmon.battle.factories import create_trainer_battle, create_wild_battle
from pythmon.save.profile import PlayerProfile


class BattleTests(unittest.TestCase):
    def test_factories_reuse_profile_creature(self) -> None:
        profile = PlayerProfile()
        self.assertIs(create_wild_battle(profile).player, profile.active_creature)
        self.assertIs(create_trainer_battle(profile).player, profile.active_creature)

    def test_player_damage_can_defeat_enemy(self) -> None:
        battle = create_wild_battle(PlayerProfile())
        battle.enemy.current_hp = 1
        battle.use_player_move(battle.player.moves[0])
        self.assertTrue(battle.won)
        self.assertTrue(battle.finished)

    def test_complete_turn_damages_both_creatures(self) -> None:
        battle = create_wild_battle(PlayerProfile())
        player_hp = battle.player.current_hp
        enemy_hp = battle.enemy.current_hp
        battle.use_move(battle.player.moves[0])
        self.assertLess(battle.player.current_hp, player_hp)
        self.assertLess(battle.enemy.current_hp, enemy_hp)


if __name__ == "__main__":
    unittest.main()
