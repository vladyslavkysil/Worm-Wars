"""
Лабораторна робота 1: Основи Python
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
"""

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 0.3
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


def create_damage_calculator():
    total_damage_dealt: int = 0

    def apply_hit(base_dmg: int, *, critical_multiplier: float = 1.0) -> int:
        nonlocal total_damage_dealt
        calc = lambda b, m: int(b * m)
        dmg = calc(base_dmg, critical_multiplier)
        total_damage_dealt += dmg
        return dmg

    return apply_hit


def input_command() -> str:
    raw = input("\nОберіть дію (A - вліво, D - вправо, F - постріл, Q - здатися): ") 
    return raw.strip().upper()


def main() -> None:
    width: int = 50
    height: int = 12
    board: list[list[str]] = [["." for _ in range(width)] for _ in range(height)]
    dmg_engine = create_damage_calculator()
    check_air_purity(["".join(r) for r in board])
    render_battlefield([" ".join(row) for row in board])


if __name__ == "__main__":
    main()