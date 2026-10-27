"""Factories for creating battles without coupling them to the UI."""

from __future__ import annotations

from pythmon.battle.battle import Battle
from pythmon.battle.creatures import Creature, nullimp
from pythmon.save.profile import PlayerProfile


def create_wild_battle(profile: PlayerProfile) -> Battle:
    """Create the first wild encounter using the profile's active creature."""
    return Battle(
        profile.active_creature,
        nullimp(),
        player_move_uses=profile.active_move_uses(),
    )


def create_trainer_battle(
    profile: PlayerProfile,
    opponent: Creature | None = None,
) -> Battle:
    """Create a trainer battle with an explicit or default opponent."""
    return Battle(
        profile.active_creature,
        opponent or nullimp(),
        player_move_uses=profile.active_move_uses(),
    )
