"""
Лабораторна робота 2: Структури даних та файлові операції
Проєкт: Worms 2D: Console Artillery (Random Procedural Terrain)
"""

import math
import os
import random
import time
from datetime import datetime

GAME_TITLE: str = "Worms 2D: Console Artillery"
GAME_VERSION: float = 2.1


TILES: dict[str, dict[str, str | bool]] = {
    ".": {"name": "повітря", "passable": True, "destructible": False, "stops_shot": False},
    "*": {"name": "снаряд", "passable": True, "destructible": False, "stops_shot": False},
    "#": {"name": "земля", "passable": False, "destructible": True, "stops_shot": True},
    "X": {"name": "бетон", "passable": False, "destructible": False, "stops_shot": True},
    "1": {"name": "гравець 1", "passable": False, "destructible": False, "stops_shot": True},
    "2": {"name": "гравець 2", "passable": False, "destructible": False, "stops_shot": True},
}



MOVE_KEYS: dict[str, tuple[int, int]] = {
    "A": (-1, 0),
    "D": (1, 0),
}

# zalaz  na  1  kl
STEP_UP: tuple[int, int] = (0, -1)


def tile_prop(char: str, prop: str) -> bool:
    """Повертає властивість клітинки зі словника TILES (невідомий символ - як стіна)."""
    return bool(TILES.get(char, TILES["X"])[prop])


def clear_screen() -> None:
    """Очищення вікна термінала для Windows та Unix/Linux/macOS."""
    os.system("cls" if os.name == "nt" else "clear")


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

    # Нижній ряд - бетонна основа, яку не можна пробити
    board[height - 1] = ["X" for _ in range(width)]

    return board


# Символи, які дозволені на карті у файлі рівня (множина - швидка перевірка "in")
MAP_CHARS: set[str] = {".", "#", "X"}


def load_level(path: str) -> dict:

    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    header: dict[str, str] = {}
    map_rows: list[str] = []
    in_map = False

    for raw_line in lines:
        line = raw_line.strip()
        if not in_map:
            if line == "" or line.startswith("#"):
                continue
            if line == "---":
                in_map = True
                continue
            if ":" not in line:
                raise ValueError(f"Незрозумілий рядок заголовка: '{line}'")
            key, value = line.split(":", 1)
            header[key.strip()] = value.strip()
        elif line:
            map_rows.append(line)

    if not map_rows:
        raise ValueError("У файлі немає карти після ---")

    width = len(map_rows[0])
    for row_num, row in enumerate(map_rows, start=1):
        if len(row) != width:
            raise ValueError(f"Рядок карти {row_num} має довжину {len(row)}, а треба {width}")
        bad_chars = set(row) - MAP_CHARS
        if bad_chars:
            raise ValueError(f"Невідомі символи в рядку {row_num}: {', '.join(sorted(bad_chars))}")

    try:
        spawns = (int(header["spawn1"]), int(header["spawn2"]))
    except KeyError as missing:
        raise ValueError(f"У заголовку немає ключа {missing}")
    except ValueError:
        raise ValueError("spawn1 і spawn2 мають бути цілими числами")

    for spawn_x in spawns:
        if not 0 <= spawn_x < width:
            raise ValueError(f"Точка появи x={spawn_x} за межами карти (ширина {width})")

    board = [list(row) for row in map_rows]
    return {"name": header.get("name", path), "board": board, "spawns": spawns}


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
    while cur_y + 1 < height and tile_prop(board[cur_y + 1][x], "passable"):
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

    while True:
        curr_x += vx
        curr_y += vy
        vy += g
        vx += wind

        ix, iy = int(round(curr_x)), int(round(curr_y))

        #Vilit
        if not (0 <= ix < width and 0 <= iy < height):
            if iy >= height or ix < 0 or ix >= width:
                for px, py, old_char in prev_coords:
                    board[py][px] = old_char
                return None
            continue

        # popal
        if tile_prop(board[iy][ix], "stops_shot"):
            for px, py, old_char in prev_coords:
                board[py][px] = old_char
            return ix, iy

        # traektoria
        if board[iy][ix] == ".":
            prev_coords.append((ix, iy, "."))
            board[iy][ix] = "*"
            clear_screen()
            print("[ПОСТРІЛ] Снаряд у польоті...")
            render_battlefield([" ".join(row) for row in board])
            time.sleep(0.03)


def create_game_state(board: list[list[str]], spawns: tuple[int, int], level_name: str) -> dict:
    
    height = len(board)
    width = len(board[0])

    state: dict = {
        "level_name": level_name,
        "board": board,
        "width": width,
        "height": height,
        "turn": 0,
        "status": "",
        "players": {
            1: {"x": spawns[0], "y": 0, "hp": 100},
            2: {"x": spawns[1], "y": 0, "hp": 100},
        },
    }

    for pid, worm in state["players"].items():
        worm["y"] = apply_gravity_to_worm(worm["x"], 0, board, height)
        board[worm["y"]][worm["x"]] = str(pid)

    return state


def move_worm(state: dict, pid: int, dx: int, dy: int) -> str:
    
    board = state["board"]
    width, height = state["width"], state["height"]
    worm = state["players"][pid]
    cur_x, cur_y = worm["x"], worm["y"]
    nx, ny = cur_x + dx, cur_y + dy

    if not validate_coordinates(nx, ny, width, height):
        return "[МЕЖА] Досягнуто межі карти!"

    climbed = False
    if not tile_prop(board[ny][nx], "passable"):
        sx, sy = STEP_UP
        up_y = ny + sy
        if (
            validate_coordinates(nx + sx, up_y, width, height)
            and tile_prop(board[up_y][nx + sx], "passable")
            and tile_prop(board[cur_y + sy][cur_x], "passable")
        ):
            ny = up_y
            climbed = True

    if not tile_prop(board[ny][nx], "passable"):
        return "[БЛОК] Попереду височина!"

    board[cur_y][cur_x] = "."
    worm["x"] = nx
    worm["y"] = apply_gravity_to_worm(nx, ny, board, height)
    board[worm["y"]][nx] = str(pid)

    action = "заліз на сходинку" if climbed else "перемістився"
    return f"[РУХ] Гравець {pid} {action}."


def explode(state: dict, ix: int, iy: int, dmg_engine) -> str:
    #Вибух: руйнує землю, наносить шкоду і заново застосовує гравітацію
    board = state["board"]
    width, height = state["width"], state["height"]
    event_logs = [f"[ВИБУХ] Влучання в координатах ({ix}, {iy})!"]

    # Деформація породи вибухом
    for by in range(max(0, iy - 1), min(height, iy + 2)):
        for bx in range(max(0, ix - 1), min(width, ix + 2)):
            if tile_prop(board[by][bx], "destructible"):
                board[by][bx] = "."

    for pid, worm in state["players"].items():
        # uron
        if abs(ix - worm["x"]) <= 2 and abs(iy - worm["y"]) <= 2:
            loss = dmg_engine(35, critical_multiplier=1.2)
            worm["hp"] -= loss
            event_logs.append(f"[УШКОДЖЕННЯ] Гравець {pid} втратив {loss} HP!")

        # черв'як падає, якщо під ним вибило землю
        if board[worm["y"]][worm["x"]] == str(pid):
            board[worm["y"]][worm["x"]] = "."
        worm["y"] = apply_gravity_to_worm(worm["x"], worm["y"], board, height)
        board[worm["y"]][worm["x"]] = str(pid)

    return "\n".join(event_logs)


def fire(state: dict, pid: int, wind: float, dmg_engine) -> str:
    
    try:
        angle = float(input("Кут нахилу ствола (наприклад, 45 градусів): "))
    except ValueError:
        angle = 45.0

    try:
        power = float(input("Сила пострілу (від 1.5 до 4.5): "))
    except ValueError:
        power = 3.0

    worm = state["players"][pid]
    shoot_dir = 1 if pid == 1 else -1

    impact = simulate_and_draw_shot(
        worm["x"], worm["y"] - 1, angle, power, shoot_dir, wind,
        state["board"], state["width"], state["height"],
    )

    if impact is None:
        return "[ПРОМАХ] Снаряд полетів за межі зони!"
    return explode(state, impact[0], impact[1], dmg_engine)


def get_winner_text(state: dict) -> str | None:
    
    hp1 = state["players"][1]["hp"]
    hp2 = state["players"][2]["hp"]
    if hp1 <= 0 and hp2 <= 0:
        return "Нічия! Обидва черв'яки знищені!"
    if hp1 <= 0:
        return "ПЕРЕМОГА ГРАВЦЯ 2!"
    if hp2 <= 0:
        return "ПЕРЕМОГА ГРАВЦЯ 1!"
    return None



LEVEL_FILE: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels", "level1.txt")


def choose_map() -> dict:
    """Меню вибору карти: рівень з файлу або випадкова генерація."""
    clear_screen()
    print("=== Worms Duel Console Edition ===")
    print(f"1 - карта з файлу ({LEVEL_FILE})")
    print("R - випадкова карта")
    choice = input("Ваш вибір: ").strip().upper()

    if choice == "1":
        try:
            return load_level(LEVEL_FILE)
        except FileNotFoundError:
            print(f"[ПОМИЛКА] Файл {LEVEL_FILE} не знайдено. Генерую випадкову карту.")
        except ValueError as error:
            print(f"[ПОМИЛКА] Рівень пошкоджений: {error}. Генерую випадкову карту.")
        time.sleep(2)

    width, height = 50, 12
    return {
        "name": "Випадкова карта",
        "board": generate_procedural_terrain(width, height),
        "spawns": (5, width - 6),
    }


SCORES_FILE: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.txt")


# дописуємо результат в кінець файлу, режим "a" не стирає старі рекорди
def save_record(winner: str, turns: int, level_name: str, hp_left: int) -> None:
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    fields = [date, winner, str(turns), level_name, str(hp_left)]
    with open(SCORES_FILE, "a", encoding="utf-8") as file:
        file.write(";".join(fields) + "\n")


# читаємо рекорди з файлу, биті рядки пропускаємо
def load_records() -> list[tuple[str, str, int, str, int]]:
    records: list[tuple[str, str, int, str, int]] = []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(";")
                if len(parts) != 5:
                    continue
                date, winner, turns, level_name, hp_left = parts
                try:
                    records.append((date, winner, int(turns), level_name, int(hp_left)))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return records


# топ перемог: менше ходів - вище, при рівності вище той, у кого більше HP
def show_top_records(limit: int = 5) -> None:
    wins = [r for r in load_records() if r[1] != "Нічия"]
    wins.sort(key=lambda r: (r[2], -r[4]))

    print("\n=== ТОП ПЕРЕМОГ (найменше ходів) ===")
    if not wins:
        print("Поки що рекордів немає.")
        return
    for place, (date, winner, turns, level_name, hp_left) in enumerate(wins[:limit], start=1):
        print(f"{place}. {winner} - {turns} ходів, {hp_left} HP ({level_name}, {date})")


def main() -> None:
    level = choose_map()
    state = create_game_state(level["board"], level["spawns"], level["name"])
    dmg_engine = create_damage_calculator()

    clear_screen()
    print(f"=== Worms Duel Console Edition: {state['level_name']} ===")
    check_air_purity(["".join(r) for r in state["board"]])
    time.sleep(1.2)

    while True:
        state["turn"] += 1
        turn = state["turn"]
        active_player = 1 if (turn % 2 != 0) else 2
        wind_speed: float = round(0.02 * math.sin(turn * 1.7), 3)

        clear_screen()
        render_battlefield([" ".join(row) for row in state["board"]])
        print(f"Хід №{turn} | Черга: Гравець {active_player}")
        print(f"Вітер: {wind_speed:+} (впливає на дальність)")
        p1, p2 = state["players"][1], state["players"][2]
        print(f"Гравець 1 (1): {p1['hp']} HP | Гравець 2 (2): {p2['hp']} HP")
        if state["status"]:
            print(f"\n{state['status']}")
            state["status"] = ""

        cmd = input_command()

        if cmd == "Q":
            # Здача не йде в рекорди, інакше "перемога за 1 хід" буде найкращою
            print(f"\nКінець гри: Гравець {active_player} здався!")
            break
        elif cmd in MOVE_KEYS:
            dx, dy = MOVE_KEYS[cmd]
            state["status"] = move_worm(state, active_player, dx, dy)
        elif cmd == "F":
            state["status"] = fire(state, active_player, wind_speed, dmg_engine)
        else:
            state["status"] = "[ПОМИЛКА] Невідома дія! Хід пропущено."

        result = get_winner_text(state)
        if result is not None:
            clear_screen()
            render_battlefield([" ".join(row) for row in state["board"]])
            print(f"\n[РЕЗУЛЬТАТ] {result}")

            p1_hp, p2_hp = state["players"][1]["hp"], state["players"][2]["hp"]
            if p1_hp <= 0 and p2_hp <= 0:
                save_record("Нічия", turn, state["level_name"], 0)
            elif p2_hp <= 0:
                save_record("Гравець 1", turn, state["level_name"], p1_hp)
            else:
                save_record("Гравець 2", turn, state["level_name"], p2_hp)
            break

    show_top_records()


if __name__ == "__main__":
    main()
