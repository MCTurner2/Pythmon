"""In-memory player progress used by the current game session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pythmon.battle.creatures import Creature, bytebug


@dataclass
class PlayerProfile:
    """Own the player's party and inventory independently of presentation."""

    party: list[Creature] = field(default_factory=lambda: [bytebug()])
    inventory: dict[str, int] = field(
        default_factory=lambda: {"Heal Patch": 3}
    )
    active_index: int = 0
    move_uses: dict[str, int] = field(default_factory=dict)

    @property
    def active_creature(self) -> Creature:
        """Return the creature currently sent into battle."""
        return self.party[self.active_index]

    def set_active_creature(self, index: int) -> None:
        """Move a party member into the active battle position."""
        if not 0 <= index < len(self.party):
            raise IndexError("party index is outside the party")
        self.active_index = index

    def active_move_uses(self) -> dict[object, int]:
        """Return the active creature's saved move uses keyed by move object."""
        creature = self.active_creature
        return {
            move: self.move_uses.get(
                self._move_key(move.name),
                move.max_uses,
            )
            for move in creature.moves
        }

    def update_active_move_uses(self, uses: dict[object, int]) -> None:
        """Store the active creature's current move uses."""
        for move, remaining in uses.items():
            self.move_uses[self._move_key(move.name)] = remaining

    def _move_key(self, move_name: str) -> str:
        """Build a stable save key for a party member's move."""
        return f"{self.active_index}:{move_name}"

    def heal_active_creature(self, amount: int = 10) -> bool:
        """Restore HP and consume one Heal Patch when possible."""
        if self.inventory.get("Heal Patch", 0) <= 0:
            return False
        creature = self.active_creature
        if creature.current_hp >= creature.max_hp:
            return False
        creature.current_hp = min(creature.max_hp, creature.current_hp + amount)
        self.inventory["Heal Patch"] -= 1
        return True

    def restore_party(self) -> None:
        """Restore all party HP and move uses without consuming items."""
        for index, creature in enumerate(self.party):
            creature.current_hp = creature.max_hp
            for move in creature.moves:
                self.move_uses.pop(f"{index}:{move.name}", None)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible player progress."""
        return {
            "version": 1,
            "active_index": self.active_index,
            "inventory": dict(self.inventory),
            "move_uses": dict(self.move_uses),
            "party": [
                {
                    "name": creature.name,
                    "level": creature.level,
                    "max_hp": creature.max_hp,
                    "current_hp": creature.current_hp,
                    "attack": creature.attack,
                    "defense": creature.defense,
                    "moves": [
                        {
                            "name": move.name,
                            "power": move.power,
                            "description": move.description,
                            "max_uses": move.max_uses,
                        }
                        for move in creature.moves
                    ],
                }
                for creature in self.party
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerProfile:
        """Build a profile from validated JSON-compatible data."""
        if data.get("version") != 1:
            raise ValueError("unsupported profile version")
        from pythmon.battle.moves import Move

        party = []
        for raw_creature in data.get("party", []):
            moves = tuple(Move(**raw_move) for raw_move in raw_creature["moves"])
            party.append(
                Creature(
                    name=raw_creature["name"],
                    level=raw_creature["level"],
                    max_hp=raw_creature["max_hp"],
                    current_hp=raw_creature["current_hp"],
                    attack=raw_creature["attack"],
                    defense=raw_creature["defense"],
                    moves=moves,
                )
            )
        if not party:
            raise ValueError("profile must contain at least one creature")
        active_index = data.get("active_index", 0)
        if not 0 <= active_index < len(party):
            raise ValueError("active_index is outside the party")
        inventory = data.get("inventory", {})
        if not isinstance(inventory, dict):
            raise ValueError("inventory must be an object")
        move_uses = data.get("move_uses", {})
        if not isinstance(move_uses, dict):
            raise ValueError("move_uses must be an object")
        return cls(
            party=party,
            inventory={str(name): int(count) for name, count in inventory.items()},
            active_index=active_index,
            move_uses={
                str(name): int(remaining)
                for name, remaining in move_uses.items()
            },
        )
