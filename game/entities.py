class Entity:
    symbol: str = "?"

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def cells(self) -> list[tuple[int, int]]:
        return [(self.x, self.y)]

    def occupies(self, x: int, y: int) -> bool:
        return (x, y) in self.cells()

    def blocks_move(self) -> bool:
        return True

    def stops_shot(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return f"{type(self).__name__}(x={self.x}, y={self.y})"


class Worm(Entity):
    MAX_HP: int = 100

    def __init__(self, pid: int, x: int, y: int, hp: int = MAX_HP) -> None:
        super().__init__(x, y)
        self.pid = pid
        self.hp = hp

    @property
    def symbol(self) -> str:
        return str(self.pid)

    @property
    def name(self) -> str:
        return f"Гравець {self.pid}"

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        lost = min(max(amount, 0), max(self.hp, 0))
        self.hp -= lost
        return lost

    def __str__(self) -> str:
        return f"{self.name} ({self.hp} HP)"

    def __repr__(self) -> str:
        return f"Worm(pid={self.pid}, x={self.x}, y={self.y}, hp={self.hp})"


class Projectile(Entity):
    symbol = "*"

    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        super().__init__(round(x), round(y))
        self.fx = x
        self.fy = y
        self.vx = vx
        self.vy = vy

    def step(self, gravity: float, wind: float) -> tuple[int, int]:
        self.fx += self.vx
        self.fy += self.vy
        self.vy += gravity
        self.vx += wind
        self.x = round(self.fx)
        self.y = round(self.fy)
        return self.x, self.y

    def blocks_move(self) -> bool:
        return False

    def stops_shot(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            f"Projectile(x={self.fx:.2f}, y={self.fy:.2f}, "
            f"vx={self.vx:.2f}, vy={self.vy:.2f})"
        )
