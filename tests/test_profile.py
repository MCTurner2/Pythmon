"""Automated tests for party and inventory persistence."""

import tempfile
import unittest
from pathlib import Path

from pythmon.save.profile import PlayerProfile
from pythmon.save.storage import load_profile, save_profile


class ProfileTests(unittest.TestCase):
    def test_heal_patch_restores_hp_and_is_consumed(self) -> None:
        profile = PlayerProfile()
        profile.active_creature.current_hp = 10
        self.assertTrue(profile.heal_active_creature())
        self.assertEqual(profile.active_creature.current_hp, 20)
        self.assertEqual(profile.inventory["Heal Patch"], 2)

    def test_profile_round_trips_through_json(self) -> None:
        profile = PlayerProfile()
        profile.active_creature.current_hp = 17
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            save_profile(profile, path)
            loaded = load_profile(path)
        self.assertEqual(loaded.active_creature.name, "Bytebug")
        self.assertEqual(loaded.active_creature.current_hp, 17)
        self.assertEqual(loaded.inventory["Heal Patch"], 3)

    def test_restore_party_restores_hp_and_move_uses(self) -> None:
        profile = PlayerProfile()
        profile.active_creature.current_hp = 1
        move = profile.active_creature.moves[0]
        profile.move_uses["0:Print"] = 2
        profile.restore_party()
        self.assertEqual(profile.active_creature.current_hp, 28)
        self.assertNotIn("0:Print", profile.move_uses)


if __name__ == "__main__":
    unittest.main()
