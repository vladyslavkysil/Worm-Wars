from game import storage
from game.console import ConsoleRenderer, KEY_COMMANDS, read_key, read_number
from game.engine import Game
from game.exceptions import GameException, InvalidMoveError
from game.levels import load_catalog, load_catalog_level, load_level, make_random_level
from game.paths import TEST_LEVEL_FILE


class State:
    def run(self, app: "ConsoleApp") -> "State | None":
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class MenuState(State):
    def __init__(self, error: str = "") -> None:
        self.error = error

    def run(self, app: "ConsoleApp") -> State | None:
        app.renderer.draw_menu(app.catalog, storage.has_save(), self.error)
        key = read_key()
        if key == "q":
            return None
        try:
            game = self.make_game(app, key)
        except (OSError, GameException) as problem:
            return MenuState(f"[ПОМИЛКА] Не вдалося завантажити: {problem}")
        if game is None:
            return MenuState("[ПОМИЛКА] Немає такого пункту меню.")
        return PlayState(game)

    def make_game(self, app: "ConsoleApp", key: str) -> Game | None:
        if key == "l" and storage.has_save():
            return storage.load_game()
        if key == "t":
            return Game.from_level(load_level(TEST_LEVEL_FILE))
        if key == "r":
            return Game.from_level(make_random_level())
        if key.isdigit() and 1 <= int(key) <= len(app.catalog):
            return Game.from_level(load_catalog_level(app.catalog, int(key) - 1))
        return None


class PlayState(State):
    def __init__(self, game: Game, status: str = "") -> None:
        self.game = game
        self.status = status

    def run(self, app: "ConsoleApp") -> State | None:
        app.renderer.draw_game(self.game, self.status)
        command = KEY_COMMANDS.get(read_key())
        if command == "PAUSE":
            return PauseState(self.game)

        try:
            self.status = self.handle(app, command)
        except InvalidMoveError as problem:
            self.status = f"[БЛОК] {problem}. Спробуйте ще раз."

        if self.game.is_over:
            record = storage.record_from_game(self.game)
            if record is not None:
                storage.save_record(record)
            return GameOverState(self.game)
        return self

    def handle(self, app: "ConsoleApp", command: str | None) -> str:
        if command == "LEFT":
            return app.renderer.describe_move(self.game.move(-1))
        if command == "RIGHT":
            return app.renderer.describe_move(self.game.move(1))
        if command == "FIRE":
            return self.fire(app)
        if command == "SAVE":
            storage.save_game(self.game)
            return "[ЗБЕРЕЖЕНО] Гру записано у savegame.json"
        if command == "QUIT":
            self.game.surrender()
            return ""
        return "[ПОМИЛКА] Невідома клавіша."

    def fire(self, app: "ConsoleApp") -> str:
        print(f"Постріл! Сила від {Game.POWER_MIN} до {Game.POWER_MAX}.")
        angle = read_number("Кут нахилу ствола (наприклад, 45): ", 45.0)
        power = read_number("Сила пострілу: ", 3.0)
        frame = app.renderer.capture(self.game)
        shot = self.game.fire(angle, power)
        app.renderer.animate_shot(frame, shot)
        return app.renderer.describe_shot(shot)


class PauseState(State):
    def __init__(self, game: Game) -> None:
        self.game = game

    def run(self, app: "ConsoleApp") -> State | None:
        app.renderer.draw_pause(self.game)
        key = read_key()
        if key == "p":
            return PlayState(self.game, "[ГРА] Продовжуємо.")
        if key == "m":
            return MenuState()
        return self


class GameOverState(State):
    def __init__(self, game: Game) -> None:
        self.game = game

    def next_index(self, app: "ConsoleApp") -> int | None:
        index = self.game.level_index
        if index is None or self.game.surrendered is not None:
            return None
        if index + 1 >= len(app.catalog):
            return None
        return index + 1

    def run(self, app: "ConsoleApp") -> State | None:
        next_index = self.next_index(app)
        app.renderer.draw_game_over(self.game, storage.top_records(), next_index is not None)
        key = read_key()
        if key == "n" and next_index is not None:
            try:
                return PlayState(Game.from_level(load_catalog_level(app.catalog, next_index)))
            except (OSError, GameException) as problem:
                return MenuState(f"[ПОМИЛКА] Наступний рівень не завантажився: {problem}")
        if key == "m":
            return MenuState()
        if key == "q":
            return None
        return self


class ConsoleApp:
    def __init__(self) -> None:
        self.renderer = ConsoleRenderer()
        self.catalog: list[dict[str, str]] = []

    def run(self) -> None:
        error = ""
        try:
            self.catalog = load_catalog()
        except (OSError, GameException) as problem:
            error = f"[ПОМИЛКА] Каталог рівнів недоступний: {problem}"

        state: State | None = MenuState(error)
        while state is not None:
            state = state.run(self)


def main() -> None:
    ConsoleApp().run()
