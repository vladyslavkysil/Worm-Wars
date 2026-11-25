import msvcrt
import os
import sys
import time

from game.engine import Game, MoveResult, ShotResult
from game.storage import Record

TITLE = "=== Worms 2D: Console Artillery (v3.0) ==="

HOME = "\x1b[H"
CLEAR_LINE = "\x1b[K"
CLEAR_BELOW = "\x1b[J"
RESET = "\x1b[0m"

COLORS = {
    "#": "\x1b[33m",
    "X": "\x1b[37m",
    "1": "\x1b[91m",
    "2": "\x1b[94m",
    "*": "\x1b[97m",
    "@": "\x1b[93m",
}

KEY_COMMANDS = {
    "a": "LEFT",
    "d": "RIGHT",
    "LEFT_ARROW": "LEFT",
    "RIGHT_ARROW": "RIGHT",
    "f": "FIRE",
    "s": "SAVE",
    "p": "PAUSE",
    "q": "QUIT",
}

Frame = list[list[str]]


def read_key() -> str:
    char = msvcrt.getwch()
    if char in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        if code == "K":
            return "LEFT_ARROW"
        if code == "M":
            return "RIGHT_ARROW"
        return ""
    return char.lower()


def read_number(prompt: str, default: float) -> float:
    try:
        return float(input(prompt))
    except ValueError:
        return default


class ConsoleRenderer:
    def __init__(self, frame_delay: float = 0.03) -> None:
        self.frame_delay = frame_delay
        os.system("")

    def clear(self) -> None:
        print("\x1b[2J" + HOME, end="", flush=True)

    def _write(self, lines: list[str]) -> None:
        text = ""
        for line in lines:
            text += line + CLEAR_LINE + "\n"
        sys.stdout.write(HOME + text + CLEAR_BELOW)
        sys.stdout.flush()

    def capture(self, game: Game) -> Frame:
        frame = [list(row) for row in game.field.to_rows()]
        for worm in game.worms.values():
            frame[worm.y][worm.x] = worm.symbol
        return frame

    def _field_lines(self, frame: Frame) -> list[str]:
        lines = [TITLE]
        for row in frame:
            cells = []
            for char in row:
                if char in COLORS:
                    cells.append(COLORS[char] + char + RESET)
                else:
                    cells.append(char)
            lines.append(" ".join(cells))
        lines.append("=" * len(TITLE))
        return lines

    def _info_lines(self, game: Game) -> list[str]:
        worm1, worm2 = game.worms[1], game.worms[2]
        return [
            f"Карта: {game.level_name} | Хід №{game.turn} | Черга: {game.active_worm.name}",
            f"Вітер: {game.wind:+}",
            f"Гравець 1: {worm1.hp} HP | Гравець 2: {worm2.hp} HP",
        ]

    def draw_game(self, game: Game, status: str = "") -> None:
        lines = self._field_lines(self.capture(game)) + self._info_lines(game)
        lines += ["", status, ""]
        lines.append("A/D або стрілки - рух | F - постріл | S - зберегти | P - пауза | Q - здатися")
        self._write(lines)

    def draw_pause(self, game: Game) -> None:
        lines = self._field_lines(self.capture(game)) + self._info_lines(game)
        lines += ["", "=== ПАУЗА ===", "P - продовжити | M - головне меню"]
        self._write(lines)

    def animate_shot(self, frame: Frame, shot: ShotResult) -> None:
        for x, y in shot.trajectory:
            frame[y][x] = "*"
            self._write(self._field_lines(frame) + ["[ПОСТРІЛ] Снаряд у польоті..."])
            time.sleep(self.frame_delay)
        if shot.impact is not None:
            x, y = shot.impact
            frame[y][x] = "@"
            self._write(self._field_lines(frame) + ["[ВИБУХ] Бабах!"])
            time.sleep(0.3)

    def describe_move(self, move: MoveResult) -> str:
        if move.climbed:
            return f"[РУХ] Гравець {move.pid} заліз на сходинку."
        return f"[РУХ] Гравець {move.pid} перемістився."

    def describe_shot(self, shot: ShotResult) -> str:
        if shot.impact is None:
            return "[ПРОМАХ] Снаряд полетів за межі зони!"
        text = f"[ВИБУХ] Влучання в координатах {shot.impact}!"
        for pid, lost in shot.damage.items():
            text += f"\n[УШКОДЖЕННЯ] Гравець {pid} втратив {lost} HP!"
        return text

    def draw_menu(self, catalog: list[dict[str, str]], has_save: bool, error: str = "") -> None:
        lines = [TITLE, ""]
        for num, item in enumerate(catalog, start=1):
            lines.append(f"{num} - {item['title']}")
        lines.append("T - Тест: карта з бетонною стіною")
        lines.append("R - випадкова карта")
        if has_save:
            lines.append("L - продовжити збережену гру")
        lines.append("Q - вихід")
        lines += ["", error, "Ваш вибір:"]
        self.clear()
        self._write(lines)

    def draw_game_over(self, game: Game, records: list[Record], has_next: bool) -> None:
        winner = game.winner
        if game.surrendered is not None:
            result = f"Гравець {game.surrendered} здався!"
        elif winner is None:
            result = "Нічия! Обидва черв'яки знищені!"
        else:
            result = f"ПЕРЕМОГА: {winner.name}!"

        lines = self._field_lines(self.capture(game)) + self._info_lines(game)
        lines += ["", f"[РЕЗУЛЬТАТ] {result}", "", "=== ТОП ПЕРЕМОГ ==="]
        if not records:
            lines.append("Поки що рекордів немає.")
        for place, record in enumerate(records, start=1):
            lines.append(f"{place}. {record}")
        lines.append("")
        if has_next:
            lines.append("N - наступний рівень | M - головне меню | Q - вихід")
        else:
            lines.append("M - головне меню | Q - вихід")
        self._write(lines)

    def __repr__(self) -> str:
        return f"ConsoleRenderer(frame_delay={self.frame_delay})"
