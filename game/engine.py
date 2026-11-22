import math
from dataclasses import dataclass, field as dataclass_field
from typing import Any

from game.entities import Projectile, Worm
from game.exceptions import InvalidMoveError, SaveFormatError
from game.field import Field
from game.levels import Level

SAVE_VERSION: int = 3


@dataclass
class MoveResult:
    pid: int
    start: tuple[int, int]
    end: tuple[int, int]
    climbed: bool


@dataclass
class ShotResult:
    pid: int
    trajectory: list[tuple[int, int]] = dataclass_field(default_factory=list)
    impact: tuple[int, int] | None = None
    destroyed: int = 0
    damage: dict[int, int] = dataclass_field(default_factory=dict)

    @property
    def missed(self) -> bool:
        return self.impact is None


class Game:
    GRAVITY: float = 0.22
    POWER_MIN: float = 1.5
    POWER_MAX: float = 4.5
    BLAST_RADIUS: int = 1
    DAMAGE_RADIUS: int = 2
    BASE_DAMAGE: int = 35
    CRIT_MULTIPLIER: float = 1.2
    MAX_SHOT_STEPS: int = 10_000

    def __init__(
        self,
        field: Field,
        worms: list[Worm],
        level_name: str,
        level_index: int | None = None,
        turn: int = 1,
    ) -> None:
        if sorted(worm.pid for worm in worms) != [1, 2]:
            raise ValueError("Потрібно рівно два черв'яки з номерами 1 і 2")
        self.field = field
        self.worms: dict[int, Worm] = {worm.pid: worm for worm in worms}
        self.level_name = level_name
        self.level_index = level_index
        self.turn = turn
        self.surrendered: int | None = None
        self.total_damage = 0

    @classmethod
    def from_level(cls, level: Level) -> "Game":
        worms: list[Worm] = []
        for pid, spawn_x in enumerate(level.spawns, start=1):
            y = level.field.drop(spawn_x, 0, blocked=[worm.position for worm in worms])
            worms.append(Worm(pid, spawn_x, y))
        return cls(level.field, worms, level.name, level.index)

    @property
    def active_pid(self) -> int:
        return 1 if self.turn % 2 else 2

    @property
    def active_worm(self) -> Worm:
        return self.worms[self.active_pid]

    @property
    def wind(self) -> float:
        return round(0.02 * math.sin(self.turn * 1.7), 3)

    @property
    def is_over(self) -> bool:
        return self.surrendered is not None or any(not worm.is_alive() for worm in self.worms.values())

    @property
    def is_draw(self) -> bool:
        return self.surrendered is None and not any(worm.is_alive() for worm in self.worms.values())

    @property
    def winner(self) -> Worm | None:
        if self.surrendered is not None:
            return self.worms[3 - self.surrendered]
        alive = [worm for worm in self.worms.values() if worm.is_alive()]
        return alive[0] if len(alive) == 1 else None

    def worm_at(self, x: int, y: int) -> Worm | None:
        for worm in self.worms.values():
            if worm.occupies(x, y):
                return worm
        return None

    def is_free(self, x: int, y: int, ignore: Worm | None = None) -> bool:
        if not self.field.is_passable(x, y):
            return False
        other = self.worm_at(x, y)
        return other is None or other is ignore

    def move(self, dx: int) -> MoveResult:
        self._ensure_running()
        if dx not in (-1, 1):
            raise InvalidMoveError("Рухатися можна лише на одну клітинку вліво або вправо")

        worm = self.active_worm
        start = worm.position
        nx, ny = worm.x + dx, worm.y
        if not self.field.in_bounds(nx, ny):
            raise InvalidMoveError("Досягнуто межі карти")

        climbed = False
        if not self.is_free(nx, ny, worm):
            if self.is_free(nx, ny - 1, worm) and self.is_free(worm.x, worm.y - 1, worm):
                ny -= 1
                climbed = True
            else:
                raise InvalidMoveError("Попереду височина")

        worm.x = nx
        worm.y = self.field.drop(nx, ny, self._cells_of_others(worm))
        self._end_turn()
        return MoveResult(worm.pid, start, worm.position, climbed)

    def fire(self, angle_deg: float, power: float) -> ShotResult:
        self._ensure_running()
        if not (math.isfinite(angle_deg) and math.isfinite(power)):
            raise InvalidMoveError("Кут і сила мають бути числами")
        if not self.POWER_MIN <= power <= self.POWER_MAX:
            raise InvalidMoveError(f"Сила пострілу має бути від {self.POWER_MIN} до {self.POWER_MAX}")

        worm = self.active_worm
        direction = 1 if worm.pid == 1 else -1
        rad = math.radians(angle_deg)
        shell = Projectile(worm.x, worm.y - 1, direction * power * math.cos(rad), -power * math.sin(rad))
        result = ShotResult(worm.pid)
        wind = self.wind

        for _ in range(self.MAX_SHOT_STEPS):
            x, y = shell.step(self.GRAVITY, wind)
            if y >= self.field.height or not 0 <= x < self.field.width:
                break
            if y < 0:
                continue
            if self.field.stops_shot(x, y) or self.worm_at(x, y) is not None:
                result.impact = (x, y)
                break
            result.trajectory.append((x, y))

        if result.impact is not None:
            self._explode(result, *result.impact)
        self._end_turn()
        return result

    def surrender(self) -> Worm:
        self._ensure_running()
        self.surrendered = self.active_pid
        return self.active_worm

    def _explode(self, result: ShotResult, ix: int, iy: int) -> None:
        result.destroyed = self.field.explode(ix, iy, self.BLAST_RADIUS)
        hit = int(self.BASE_DAMAGE * self.CRIT_MULTIPLIER)

        for worm in self.worms.values():
            if abs(ix - worm.x) <= self.DAMAGE_RADIUS and abs(iy - worm.y) <= self.DAMAGE_RADIUS:
                lost = worm.take_damage(hit)
                result.damage[worm.pid] = lost
                self.total_damage += lost

        for worm in sorted(self.worms.values(), key=lambda w: -w.y):
            worm.y = self.field.drop(worm.x, worm.y, self._cells_of_others(worm))

    def _cells_of_others(self, worm: Worm) -> list[tuple[int, int]]:
        return [cell for other in self.worms.values() if other is not worm for cell in other.cells()]

    def _ensure_running(self) -> None:
        if self.is_over:
            raise InvalidMoveError("Гру вже завершено")

    def _end_turn(self) -> None:
        if not self.is_over:
            self.turn += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": SAVE_VERSION,
            "level_name": self.level_name,
            "level_index": self.level_index,
            "turn": self.turn,
            "field": self.field.to_rows(),
            "players": {
                str(pid): {"x": worm.x, "y": worm.y, "hp": worm.hp} for pid, worm in self.worms.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        try:
            version = int(data.get("version", 2))
            rows: list[str] = data["field"] if version >= 3 else data["board"]
            turn = int(data["turn"])
            if version < 3:
                rows = [row.replace("1", ".").replace("2", ".") for row in rows]
                turn += 1
            raw_index = data.get("level_index")
            level_index = None if raw_index is None else int(raw_index)
            field = Field.from_rows(rows)
            worms = [
                Worm(int(pid), int(info["x"]), int(info["y"]), int(info["hp"]))
                for pid, info in data["players"].items()
            ]
            game = cls(field, worms, str(data["level_name"]), level_index, turn)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise SaveFormatError(f"Пошкоджене збереження: {error}") from error

        for worm in game.worms.values():
            if not field.is_passable(worm.x, worm.y):
                raise SaveFormatError(f"{worm.name} не на своєму місці")
        return game

    def __str__(self) -> str:
        players = ", ".join(str(worm) for worm in self.worms.values())
        return f"{self.level_name}: хід {self.turn}, {players}"

    def __repr__(self) -> str:
        return (
            f"Game(level_name={self.level_name!r}, turn={self.turn}, "
            f"worms={list(self.worms.values())!r})"
        )
