"""
Лабораторна робота 1: Основи Python
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
Рівень: 100 балів (із золотими алгоритмічними завданнями)
"""

import math
import random
import time

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 2.1
turn_counter: int = 0


def generate_procedural_terrain(width: int, height: int) -> list[list[str]]:
    """
    ЗОЛОТЕ ЗАВДАННЯ: Рандомізована процедурна генерація рельєфу.
    При кожному запуску генерує унікальні параметри хвиль (фазовий зсув і частоту).
    """
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

        # Виліт за межі
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

        # Відображення польоту
        if board[iy][ix] == ".":
            prev_coords.append((ix, iy, "."))
            board[iy][ix] = "*"
            render_battlefield([" ".join(row) for row in board])
            time.sleep(0.03)


def main() -> None:
    global turn_counter

    width: int = 50
    height: int = 12
    game_running: bool = True
    surrender_msg: None | str = None

    hp_p1: int = 100
    hp_p2: int = 100

    
    board = generate_procedural_terrain(width, height)

    # Автоматичне знаходження поверхні для гравців 1 та 2
    p1_x = 5
    p1_y = apply_gravity_to_worm(p1_x, 0, board, height)
    board[p1_y][p1_x] = "1"

    p2_x = 44
    p2_y = apply_gravity_to_worm(p2_x, 0, board, height)
    board[p2_y][p2_x] = "2"

    dmg_engine = create_damage_calculator()

    print("=== Worms Duel Console Edition ===")
    check_air_purity(["".join(r) for r in board])

    while game_running:
        turn_counter += 1
        active_player = 1 if (turn_counter % 2 != 0) else 2

        # Динамічний вітер кожен хід
        wind_speed: float = round(0.02 * math.sin(turn_counter * 1.7), 3)

        render_battlefield([" ".join(row) for row in board])
        print(f"Хід №{turn_counter} | Черга: Гравець {active_player}")
        print(f"Вітер: {wind_speed:+} (впливає на дальність)")
        print(f"Гравець 1 (1): {hp_p1} HP | Гравець 2 (2): {hp_p2} HP")

        cmd = input_command()

        if cmd == "Q":
            surrender_msg = f"Гравець {active_player} здався!"
            break

        elif cmd in ("A", "D"):
            dx = -1 if cmd == "A" else 1
            cur_x = p1_x if active_player == 1 else p2_x
            cur_y = p1_y if active_player == 1 else p2_y
            nx = cur_x + dx

            if validate_coordinates(nx, cur_y, width, height):
                if board[cur_y][nx] == ".":
                    board[cur_y][cur_x] = "."
                    new_y = apply_gravity_to_worm(nx, cur_y, board, height)
                    board[new_y][nx] = str(active_player)

                    if active_player == 1:
                        p1_x, p1_y = nx, new_y
                    else:
                        p2_x, p2_y = nx, new_y
                    print(f"[РУХ] Гравець {active_player} перемістився.")
                else:
                    print("[БЛОК] Попереду височина!")
            else:
                print("[МЕЖА] Досягнуто межі карти!")

        elif cmd == "F":
            try:
                angle = float(input("Кут нахилу ствола (наприклад, 45 градусів): "))
            except ValueError:
                angle = 45.0

            try:
                power = float(input("Сила пострілу (від 1.5 до 4.5): "))
            except ValueError:
                power = 3.0

            cur_x = p1_x if active_player == 1 else p2_x
            cur_y = p1_y if active_player == 1 else p2_y

            shoot_dir = 1 if active_player == 1 else -1

            impact = simulate_and_draw_shot(
                cur_x, cur_y - 1, angle, power, shoot_dir, wind_speed, board, width, height
            )

            if impact is None:
                print("\n[ПРОМАХ] Снаряд полетів за межі зони!")
            else:
                ix, iy = impact
                print(f"\n[ВИБУХ] Влучання в координатах ({ix}, {iy})!")

                # Деформація породи вибухом
                for by in range(max(0, iy - 1), min(height, iy + 2)):
                    for bx in range(max(0, ix - 1), min(width, ix + 2)):
                        if board[by][bx] == "#":
                            board[by][bx] = "."

                # Шкода гравцям
                if abs(ix - p1_x) <= 2 and abs(iy - p1_y) <= 2:
                    loss = dmg_engine(35, critical_multiplier=1.2)
                    hp_p1 -= loss
                    print(f"[УШКОДЖЕННЯ] Гравець 1 втратив {loss} HP!")

                if abs(ix - p2_x) <= 2 and abs(iy - p2_y) <= 2:
                    loss = dmg_engine(35, critical_multiplier=1.2)
                    hp_p2 -= loss
                    print(f"[УШКОДЖЕННЯ] Гравець 2 втратив {loss} HP!")

                # Перерахунок положення черв'яків після вибуху
                if board[p1_y][p1_x] == "1":
                    board[p1_y][p1_x] = "."
                p1_y = apply_gravity_to_worm(p1_x, p1_y, board, height)
                board[p1_y][p1_x] = "1"

                if board[p2_y][p2_x] == "2":
                    board[p2_y][p2_x] = "."
                p2_y = apply_gravity_to_worm(p2_x, p2_y, board, height)
                board[p2_y][p2_x] = "2"
        else:
            print("[ПОМИЛКА] Невідома дія! Хід пропущено.")

        if hp_p1 <= 0 and hp_p2 <= 0:
            print("\n[РЕЗУЛЬТАТ] Нічия! Обидва черв'яки знищені!")
            game_running = False
        elif hp_p1 <= 0:
            print("\n[РЕЗУЛЬТАТ] ПЕРЕМОГА ГРАВЦЯ 2!")
            game_running = False
        elif hp_p2 <= 0:
            print("\n[РЕЗУЛЬТАТ] ПЕРЕМОГА ГРАВЦЯ 1!")
            game_running = False

    if surrender_msg is not None:
        print(f"\nКінець гри: {surrender_msg}")


if __name__ == "__main__":
    main()