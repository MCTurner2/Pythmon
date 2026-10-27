"""Reusable dialogue presentation for the overworld."""

from __future__ import annotations

import pygame


class DialogueBox:
    """Display a sequence of messages and advance them with a confirm key."""

    def __init__(self, messages: tuple[str, ...]) -> None:
        if not messages:
            raise ValueError("dialogue requires at least one message")
        self.messages = messages
        self.message_index = 0
        self.font = pygame.font.Font(None, 30)
        self.hint_font = pygame.font.Font(None, 24)

    @property
    def finished(self) -> bool:
        """Return whether the dialogue has been dismissed."""
        return self.message_index >= len(self.messages)

    def advance(self) -> None:
        """Show the next message or dismiss the dialogue."""
        self.message_index += 1

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the current message over the game world."""
        if self.finished:
            return

        margin = 32
        box = pygame.Rect(
            margin,
            surface.get_height() - 150,
            surface.get_width() - margin * 2,
            118,
        )
        pygame.draw.rect(surface, (20, 24, 36), box, border_radius=8)
        pygame.draw.rect(surface, (232, 232, 210), box, 3, border_radius=8)

        lines = _wrap_text(self.messages[self.message_index], self.font, box.width - 32)
        for line_index, line in enumerate(lines[:3]):
            rendered = self.font.render(line, True, (245, 245, 235))
            surface.blit(rendered, (box.x + 16, box.y + 14 + line_index * 30))

        hint = self.hint_font.render("E / SPACE  Continue", True, (180, 190, 202))
        surface.blit(hint, (box.right - hint.get_width() - 16, box.bottom - 28))


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap text at word boundaries so it fits inside the dialogue box."""
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join((*current, word))
        if current and font.size(candidate)[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines
