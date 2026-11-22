from pathlib import Path

PROJECT_DIR: Path = Path(__file__).resolve().parent.parent
LEVELS_DIR: Path = PROJECT_DIR / "levels"
CATALOG_FILE: Path = LEVELS_DIR / "levels.json"
TEST_LEVEL_FILE: Path = LEVELS_DIR / "test_closed.txt"
SAVE_FILE: Path = PROJECT_DIR / "savegame.json"
SCORES_FILE: Path = PROJECT_DIR / "scores.txt"
