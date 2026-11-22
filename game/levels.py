import json
import math
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from game.exceptions import GameException, LevelFormatError
from game.field import Field
from game.paths import CATALOG_FILE, LEVELS_DIR
from game.tiles import Air, Concrete, Dirt, Tile


@dataclass
class Level:
    name: str
    field: Field
    spawns: tuple[int, int]
    index: int | None = None

    def __str__(self) -> str:
        return f"Рівень «{self.name}» ({self.field.width}x{self.field.height})"


def parse_level(text: str, default_name: str = "Без назви") -> Level:
    header: dict[str, str] = {}
    map_rows: list[str] = []
    in_map = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not in_map:
            if line == "" or line.startswith("#"):
                continue
            if line == "---":
                in_map = True
                continue
            if ":" not in line:
                raise LevelFormatError(f"Незрозумілий рядок заголовка: '{line}'")
            key, value = line.split(":", 1)
            header[key.strip()] = value.strip()
        elif line:
            map_rows.append(line)

    if not map_rows:
        raise LevelFormatError("У файлі немає карти після ---")

    try:
        field = Field.from_rows(map_rows)
    except ValueError as error:
        raise LevelFormatError(str(error)) from error

    try:
        spawns = (int(header["spawn1"]), int(header["spawn2"]))
    except KeyError as missing:
        raise LevelFormatError(f"У заголовку немає ключа {missing}") from None
    except ValueError:
        raise LevelFormatError("spawn1 і spawn2 мають бути цілими числами") from None

    for spawn_x in spawns:
        if not 0 <= spawn_x < field.width:
            raise LevelFormatError(f"Точка появи x={spawn_x} за межами карти (ширина {field.width})")

    check_reachability(field, spawns)
    return Level(header.get("name", default_name), field, spawns)


def load_level(path: str | Path) -> Level:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return parse_level(text, default_name=path.stem)


def find_landings(field: Field, spawns: tuple[int, int]) -> list[tuple[int, int]]:
    landings: list[tuple[int, int]] = []
    for num, spawn_x in enumerate(spawns, start=1):
        if not field.is_passable(spawn_x, 0):
            raise LevelFormatError(f"Гравець {num} з'являється всередині землі (x={spawn_x})")
        spawn_y = field.drop(spawn_x, 0)
        if spawn_y == field.height - 1:
            raise LevelFormatError(f"Під гравцем {num} немає землі, він падає за карту")
        landings.append((spawn_x, spawn_y))
    return landings


def check_reachability(field: Field, spawns: tuple[int, int]) -> None:
    start, goal = find_landings(field, spawns)
    visited: set[tuple[int, int]] = {start}
    queue: deque[tuple[int, int]] = deque([start])

    while queue:
        cell = queue.popleft()
        if cell == goal:
            return
        for neighbor in field.get_neighbors(*cell):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    raise LevelFormatError("Гравці замуровані: між ними немає жодного шляху через повітря")


def generate_terrain(width: int, height: int, rng: random.Random | None = None) -> Field:
    rng = rng or random.Random()
    phase1 = rng.uniform(0.0, 6.28)
    phase2 = rng.uniform(0.0, 6.28)
    frequency = rng.uniform(2.5, 4.5)
    base_depth = rng.uniform(6.5, 8.5)

    tiles: list[list[Tile]] = [[Air() for _ in range(width)] for _ in range(height)]
    for x in range(width):
        angle = (x / width) * frequency * math.pi
        hill_offset = 2.2 * math.sin(angle + phase1) + 1.2 * math.cos(angle * 0.6 + phase2)
        ground_level = max(3, min(height - 2, int(base_depth + hill_offset)))
        for y in range(ground_level, height):
            tiles[y][x] = Dirt()

    tiles[height - 1] = [Concrete() for _ in range(width)]
    return Field(tiles)


def make_random_level(
    width: int = 50, height: int = 12, attempts: int = 20, rng: random.Random | None = None
) -> Level:
    spawns = (5, width - 6)
    for _ in range(attempts):
        field = generate_terrain(width, height, rng)
        try:
            check_reachability(field, spawns)
        except LevelFormatError:
            continue
        return Level("Випадкова карта", field, spawns)
    raise GameException("Не вдалося згенерувати прохідну карту")


def load_catalog(path: str | Path = CATALOG_FILE) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as error:
            raise LevelFormatError(f"Каталог рівнів пошкоджений: {error}") from error

    levels = data.get("levels") if isinstance(data, dict) else None
    if not isinstance(levels, list):
        raise LevelFormatError("У каталозі немає списку levels")
    for item in levels:
        if not isinstance(item, dict) or "file" not in item or "title" not in item:
            raise LevelFormatError("Кожен рівень у каталозі має містити file і title")
    return levels


def load_catalog_level(
    catalog: list[dict[str, str]], index: int, levels_dir: str | Path = LEVELS_DIR
) -> Level:
    level = load_level(Path(levels_dir) / catalog[index]["file"])
    level.index = index
    return level
