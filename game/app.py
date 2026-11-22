from game import storage
from game.console import ConsoleRenderer, KEY_COMMANDS, ask_yes_no, read_key, read_number
from game.engine import Game
from game.exceptions import GameException, InvalidMoveError
from game.levels import load_catalog, load_catalog_level, load_level, make_random_level
from game.paths import TEST_LEVEL_FILE


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

        game = self.choose_start(error)
        while game is not None:
            self.play(game)
            if game.surrendered is not None:
                break
            game = self.next_level(game)

    def choose_start(self, error: str) -> Game | None:
        while True:
            self.renderer.draw_menu(self.catalog, storage.has_save(), error)
            key = read_key()
            try:
                if key == "q":
                    return None
                if key == "l" and storage.has_save():
                    return storage.load_game()
                if key == "t":
                    return Game.from_level(load_level(TEST_LEVEL_FILE))
                if key == "r":
                    return Game.from_level(make_random_level())
                if key.isdigit() and 1 <= int(key) <= len(self.catalog):
                    return Game.from_level(load_catalog_level(self.catalog, int(key) - 1))
                error = "[ПОМИЛКА] Немає такого пункту меню."
            except (OSError, GameException) as problem:
                error = f"[ПОМИЛКА] Не вдалося завантажити: {problem}"

    def play(self, game: Game) -> None:
        self.renderer.clear()
        status = ""
        while not game.is_over:
            self.renderer.draw_game(game, status)
            command = KEY_COMMANDS.get(read_key())
            try:
                if command == "LEFT":
                    status = self.renderer.describe_move(game.move(-1))
                elif command == "RIGHT":
                    status = self.renderer.describe_move(game.move(1))
                elif command == "FIRE":
                    status = self.fire(game)
                elif command == "SAVE":
                    storage.save_game(game)
                    status = "[ЗБЕРЕЖЕНО] Гру записано у savegame.json"
                elif command == "QUIT":
                    game.surrender()
                else:
                    status = "[ПОМИЛКА] Невідома клавіша."
            except InvalidMoveError as problem:
                status = f"[БЛОК] {problem}. Спробуйте ще раз."

        record = storage.record_from_game(game)
        if record is not None:
            storage.save_record(record)
        self.renderer.draw_game_over(game, storage.top_records())

    def fire(self, game: Game) -> str:
        print(f"Постріл! Сила від {Game.POWER_MIN} до {Game.POWER_MAX}.")
        angle = read_number("Кут нахилу ствола (наприклад, 45): ", 45.0)
        power = read_number("Сила пострілу: ", 3.0)
        frame = self.renderer.capture(game)
        shot = game.fire(angle, power)
        self.renderer.animate_shot(frame, shot)
        return self.renderer.describe_shot(shot)

    def next_level(self, game: Game) -> Game | None:
        index = game.level_index
        if index is None:
            return None
        if index + 1 >= len(self.catalog):
            print("Ви пройшли всі рівні з каталогу!")
            return None
        title = self.catalog[index + 1]["title"]
        if not ask_yes_no(f'Перейти до наступного рівня "{title}"? (Y/N) '):
            return None
        return Game.from_level(load_catalog_level(self.catalog, index + 1))


def main() -> None:
    ConsoleApp().run()
