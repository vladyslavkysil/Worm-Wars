class GameException(Exception):
    pass


class LevelFormatError(GameException):
    pass


class InvalidMoveError(GameException):
    pass


class SaveFormatError(GameException):
    pass
