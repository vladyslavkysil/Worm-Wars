"""
Лабораторна робота 1: Основи Python
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
"""

import math
import random
import time

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 1.1
turn_counter: int = 0


def generate_procedural_terrain(width: int, height: int) -> list[list[str]]:
    board: list[list[str]] = [["." for _ in range(width)] for _ in range(height)]

    phase1: float = random.uniform(0.0, 6.28)
    phase2: float = random.uniform(0.0, 6.28)
    frequency: float = random.uniform(2.5, 4.5)
    base_depth: float = random.uniform(6.5, 8.5)

    for x in range(width):
        angle = (x / width) * frequency * math.pi
        hill_offset = 2.2 * math.sin(angle + phase1) + 1.2 * math.cos(angle * 0.6 + phase2)
        ground_level = int(base_depth + hill_offset)
        ground_level = max(3, min(height - 2, ground_level))

        for y in range(ground_level, height):
            board[y][x] = "#"

    return board


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


def apply_gravity_to_worm(x: int, y: int, board: list[list[str]], height: int) -> int:
    cur_y = y
    while cur_y + 1 < height and board[cur_y + 1][x] == ".":
        cur_y += 1
    return cur_y


def simulate_and_draw_shot(
    start_x: int,
    start_y: int,
    angle_deg: float,
    power: float,
    direction: int,
    wind: float,
    board: list[list[str]],
    width: int,
    height: int,
) -> tuple[int, int] | None:
    rad = math.radians(angle_deg)
    vx: float = direction * power * math.cos(rad)
    vy: float = -power * math.sin(rad)
    g: float = 0.22

    curr_x: float = float(start_x)
    curr_y: float = float(start_y)
    prev_coords: list[tuple[int, int, str]] = []

    print("\n[ПОСТРІЛ] Снаряд випущено...")

    while True:
        curr_x += vx
        curr_y += vy
        vy += g
        vx += wind

        ix, iy = int(round(curr_x)), int(round(curr_y))

        if not (0 <= ix < width and 0 <= iy < height):
            if iy >= height or ix < 0 or ix >= width:
                for px, py, old_char in prev_coords:
                    board[py][px] = old_char
                return None
            continue

        if board[iy][ix] in ("#", "1", "2"):
            for px, py, old_char in prev_coords:
                board[py][px] = old_char
            return ix, iy

        if board[iy][ix] == ".":
            prev_coords.append((ix, iy, "."))
            board[iy][ix] = "*"
            render_battlefield([" ".join(row) for row in board])
            time.sleep(0.03)


def main() -> None:
    width: int = 50
    height: int = 12
    board = generate_procedural_terrain(width, height)
    render_battlefield([" ".join(row) for row in board])


if __name__ == "__main__":
    main()