"""Application entry point for Pythmon."""

from game_engine.engine import GameEngine

from pythmon.game import PythmonGame

# main

def main() -> None:
    """Create the engine and run the Pythmon prototype."""
    engine = GameEngine(
        width=1280,
        height=720,
        title="Pythmon",
        frame_rate=60,
        background_color=(24, 32, 48),
    )
    engine.add_game_object(PythmonGame(engine.input))
    engine.start()


if __name__ == "__main__":
    main()
