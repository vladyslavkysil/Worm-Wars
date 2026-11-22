import json
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from game.engine import Game
from game.exceptions import SaveFormatError
from game.paths import SAVE_FILE, SCORES_FILE

DRAW: str = "Нічия"


class Record(NamedTuple):
    date: str
    winner: str
    turns: int
    level_name: str
    hp_left: int

    def __str__(self) -> str:
        return f"{self.winner} - {self.turns} ходів, {self.hp_left} HP ({self.level_name}, {self.date})"


def has_save(path: str | Path = SAVE_FILE) -> bool:
    return Path(path).exists()


def save_game(game: Game, path: str | Path = SAVE_FILE) -> Path:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(game.to_dict(), file, ensure_ascii=False, indent=2)
    return Path(path)


def load_game(path: str | Path = SAVE_FILE) -> Game:
    with open(path, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError as error:
            raise SaveFormatError(f"Файл збереження пошкоджений: {error}") from error
    if not isinstance(data, dict):
        raise SaveFormatError("Файл збереження має містити JSON-об'єкт")
    return Game.from_dict(data)


def record_from_game(game: Game) -> Record | None:
    if not game.is_over or game.surrendered is not None:
        return None
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    winner = game.winner
    if winner is None:
        return Record(date, DRAW, game.turn, game.level_name, 0)
    return Record(date, winner.name, game.turn, game.level_name, winner.hp)


def save_record(record: Record, path: str | Path = SCORES_FILE) -> None:
    with open(path, "a", encoding="utf-8") as file:
        file.write(";".join(str(value) for value in record) + "\n")


def load_records(path: str | Path = SCORES_FILE) -> list[Record]:
    records: list[Record] = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(";")
                if len(parts) != 5:
                    continue
                date, winner, turns, level_name, hp_left = parts
                try:
                    records.append(Record(date, winner, int(turns), level_name, int(hp_left)))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return records


def top_records(limit: int = 5, path: str | Path = SCORES_FILE) -> list[Record]:
    wins = [record for record in load_records(path) if record.winner != DRAW]
    wins.sort(key=lambda record: (record.turns, -record.hp_left))
    return wins[:limit]
