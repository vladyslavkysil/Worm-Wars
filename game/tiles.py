class Tile:
    char: str = "?"
    name: str = "невідома клітинка"

    def is_passable(self) -> bool:
        return False

    def stops_shot(self) -> bool:
        return True

    def on_explosion(self) -> "Tile":
        return self

    def __str__(self) -> str:
        return self.char

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other)

    def __hash__(self) -> int:
        return hash(type(self))


class Air(Tile):
    char = "."
    name = "повітря"

    def is_passable(self) -> bool:
        return True

    def stops_shot(self) -> bool:
        return False


class Dirt(Tile):
    char = "#"
    name = "земля"

    def on_explosion(self) -> Tile:
        return Air()


class Concrete(Tile):
    char = "X"
    name = "бетон"


TILE_TYPES: dict[str, type[Tile]] = {cls.char: cls for cls in (Air, Dirt, Concrete)}


def tile_from_char(char: str) -> Tile:
    try:
        return TILE_TYPES[char]()
    except KeyError:
        raise ValueError(f"Невідомий символ клітинки: '{char}'") from None
