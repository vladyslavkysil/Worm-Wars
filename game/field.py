from collections.abc import Iterable

from game.tiles import Tile, tile_from_char

NEIGHBORS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Field:
    def __init__(self, tiles: list[list[Tile]]) -> None:
        if not tiles or not tiles[0]:
            raise ValueError("Поле не може бути порожнім")
        width = len(tiles[0])
        for row_num, row in enumerate(tiles, start=1):
            if len(row) != width:
                raise ValueError(f"Рядок поля {row_num} має довжину {len(row)}, а треба {width}")
        self._tiles = tiles
        self.width = width
        self.height = len(tiles)

    @classmethod
    def from_rows(cls, rows: Iterable[str]) -> "Field":
        tiles: list[list[Tile]] = []
        for row_num, row in enumerate(rows, start=1):
            try:
                tiles.append([tile_from_char(char) for char in row])
            except ValueError as error:
                raise ValueError(f"Рядок {row_num}: {error}") from error
        return cls(tiles)

    def to_rows(self) -> list[str]:
        return ["".join(tile.char for tile in row) for row in self._tiles]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x: int, y: int) -> Tile:
        if not self.in_bounds(x, y):
            raise IndexError(f"Клітинка ({x}, {y}) за межами поля")
        return self._tiles[y][x]

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        if not self.in_bounds(x, y):
            raise IndexError(f"Клітинка ({x}, {y}) за межами поля")
        self._tiles[y][x] = tile

    def is_passable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self._tiles[y][x].is_passable()

    def stops_shot(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self._tiles[y][x].stops_shot()

    def get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        return [(x + dx, y + dy) for dx, dy in NEIGHBORS if self.is_passable(x + dx, y + dy)]

    def drop(self, x: int, y: int, blocked: Iterable[tuple[int, int]] = ()) -> int:
        occupied = set(blocked)
        while self.is_passable(x, y + 1) and (x, y + 1) not in occupied:
            y += 1
        return y

    def explode(self, cx: int, cy: int, radius: int = 1) -> int:
        destroyed = 0
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if not self.in_bounds(x, y):
                    continue
                old = self._tiles[y][x]
                new = old.on_explosion()
                if new != old:
                    self._tiles[y][x] = new
                    destroyed += 1
        return destroyed

    def __str__(self) -> str:
        return "\n".join(self.to_rows())

    def __repr__(self) -> str:
        return f"Field(width={self.width}, height={self.height})"
