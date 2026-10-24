"""
Лабораторна робота 1: Основи Python
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
"""

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 0.1
turn_counter: int = 0


def render_battlefield(sky_and_ground: list[str]) -> None:
    print(f"\n=== {GAME_TITLE} (v{GAME_VERSION}) ===")
    for row in sky_and_ground:
        print(row)
    print("=" * 55)


def validate_coordinates(x: int, y: int, width: int, height: int, /) -> bool:
    valid_x: bool = 0 <= x < width
    valid_y: bool = 0 <= y < height
    return valid_x and valid_y


def main() -> None:
    width: int = 50
    height: int = 12
    board: list[list[str]] = [["." for _ in range(width)] for _ in range(height)]
    render_battlefield([" ".join(row) for row in board])


if __name__ == "__main__":
    main()