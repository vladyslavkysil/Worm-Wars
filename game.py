"""
Лабораторна робота 1: Основи Python
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
"""

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 0.2
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


def check_air_purity(field: list[str]) -> None:
    """Сканування мапи (for, range, continue, break, for...else)."""
    for r_idx in range(len(field)):
        row = field[r_idx]
        if "#" in row:
            continue
        for char in row:
            if char == "*":
                print("[УВАГА] У повітрі помічено дим!")
                break
    else:
        print("[ІНФО] Повітря чисте, балістичні умови стабільні.")


def main() -> None:
    width: int = 50
    height: int = 12
    board: list[list[str]] = [["." for _ in range(width)] for _ in range(height)]
    check_air_purity(["".join(r) for r in board])
    render_battlefield([" ".join(row) for row in board])


if __name__ == "__main__":
    main()