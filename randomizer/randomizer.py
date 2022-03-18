import os
import shutil
import subprocess
from configparser import ConfigParser
from enum import Enum
from typing import Dict

from utils import constants


class Game(str, Enum):
    Yakuza5 = "yakuza5"
    Yakuza0 = "yakuza0"


class Randomizer:
    def __init__(self, config: ConfigParser, game: Game) -> None:
        self.config = config
        self.game = game
        self.changed_models: Dict[str, str] = {}

    def randomize(self):
        raise NotImplementedError

    def revert(self):
        raise NotImplementedError

    def _load_text(self, path: str):
        with open(path) as f:
            return [l.strip() for l in f.readlines() if l and not l.startswith("#")]

    def _backup(self, path: str):
        bak_path = f"{path}.bak"
        if os.path.exists(bak_path):
            shutil.copyfile(bak_path, path)
        else:
            shutil.copyfile(path, bak_path)

    def _extract(self, path: str):
        subprocess.run([constants.PAR_TOOL, "extract", path, constants.TMP_DIR])

    def _revert_file(self, path: str):
        bak_path = f"{path}.bak"
        if os.path.exists(bak_path):
            shutil.copyfile(bak_path, path)
