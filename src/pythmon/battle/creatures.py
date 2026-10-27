"""Creature definitions used by battles."""

from __future__ import annotations

from dataclasses import dataclass

from pythmon.battle.moves import Move


@dataclass
class Creature:
    """A battle creature with mutable hit points."""

    name: str
    level: int
    max_hp: int
    attack: int
    defense: int
    moves: tuple[Move, ...]
    current_hp: int | None = None

    def __post_init__(self) -> None:
        if self.level <= 0 or self.max_hp <= 0:
            raise ValueError("level and max_hp must be greater than zero")
        if self.attack < 0 or self.defense < 0:
            raise ValueError("attack and defense cannot be negative")
        if not self.moves:
            raise ValueError("creature must know at least one move")
        if self.current_hp is None:
            self.current_hp = self.max_hp
        if not 0 <= self.current_hp <= self.max_hp:
            raise ValueError("current_hp must be between zero and max_hp")

    @property
    def defeated(self) -> bool:
        """Return whether the creature has no hit points remaining."""
        return self.current_hp == 0


def bytebug() -> Creature:
    """Create the player's starter programming creature."""
    return Creature(
        "Bytebug",
        level=3,
        max_hp=28,
        attack=9,
        defense=5,
        moves=(
            Move("Print", 8, "Sends a bright output burst.", max_uses=15),
            Move("Debug", 11, "Finds a weakness in the target.", max_uses=8),
        ),
    )


def nullimp() -> Creature:
    """Create the first wild opponent."""
    return Creature(
        "Nullimp",
        level=2,
        max_hp=22,
        attack=6,
        defense=3,
        moves=(Move("Crash", 6, "Throws a tiny runtime error.", max_uses=20),),
    )
