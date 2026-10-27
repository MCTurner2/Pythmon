"""Battle flow and turn resolution, independent of Pygame."""

from __future__ import annotations

from pythmon.battle.creatures import Creature
from pythmon.battle.moves import Move


class Battle:
    """Resolve player and enemy turns for a one-on-one battle."""

    def __init__(
        self,
        player: Creature,
        enemy: Creature,
        player_move_uses: dict[object, int] | None = None,
    ) -> None:
        self.player = player
        self.enemy = enemy
        self.message = f"A wild {enemy.name} appeared!"
        self.finished = False
        self.won = False
        self.move_uses = {
            move: move.max_uses
            for move in (*player.moves, *enemy.moves)
        }
        if player_move_uses is not None:
            self.move_uses.update(player_move_uses)

    def remaining_uses(self, move: Move) -> int:
        """Return how many times a move can still be used this battle."""
        return self.move_uses.get(move, 0)

    def consume_move(self, move: Move) -> bool:
        """Consume one use, returning false when the move is depleted."""
        if self.remaining_uses(move) <= 0:
            return False
        self.move_uses[move] -= 1
        return True

    def use_move(self, move: Move) -> None:
        """Resolve a complete turn immediately for non-visual callers."""
        if self.use_player_move(move) and not self.finished:
            self.use_enemy_move()

    def use_player_move(self, move: Move) -> bool:
        """Apply only the player's move."""
        if self.finished:
            return False
        if not self.consume_move(move):
            self.message = f"{move.name} has no uses left."
            return False
        damage = self.player_move_damage(move)
        self.apply_player_move(move, damage)
        return True

    def player_move_damage(self, move: Move) -> int:
        """Calculate player damage without changing either creature."""
        return max(1, self.player.attack + move.power - self.enemy.defense)

    def apply_player_move(self, move: Move, damage: int) -> None:
        """Apply previously calculated player damage."""
        self.enemy.current_hp = max(0, self.enemy.current_hp - damage)
        if self.enemy.defeated:
            self.finished = True
            self.won = True
            self.message = f"{self.enemy.name} crashed! You won!"
        else:
            self.message = (
                f"{self.player.name} used {move.name}! "
                f"{self.enemy.name} lost {damage} HP."
            )

    def use_enemy_move(self) -> None:
        """Apply the enemy response after the presentation pause."""
        if self.finished:
            return
        enemy_move = self.enemy.moves[0]
        if not self.consume_move(enemy_move):
            return
        enemy_damage = self.enemy_move_damage()
        self.apply_enemy_move(enemy_move, enemy_damage)

    def enemy_move_damage(self) -> int:
        """Calculate enemy damage without changing either creature."""
        enemy_move = self.enemy.moves[0]
        return max(1, self.enemy.attack + enemy_move.power - self.player.defense)

    def apply_enemy_move(self, enemy_move: Move, damage: int) -> None:
        """Apply previously calculated enemy damage."""
        self.player.current_hp = max(0, self.player.current_hp - damage)
        if self.player.defeated:
            self.finished = True
            self.message = f"{self.player.name} ran out of memory."
            return
        self.message = (
            f"{self.enemy.name} used {enemy_move.name}! "
            f"{self.player.name} lost {damage} HP."
        )
