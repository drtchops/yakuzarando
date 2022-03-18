import json
import os
import random
import shutil
import subprocess
from configparser import ConfigParser
from typing import Any, Dict

from utils import constants, dispose_string

from .randomizer import Game, Randomizer


class Yakuza5Randomizer(Randomizer):
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config, Game.Yakuza5)
        game_dir = self.config["General"]["Yakuza5Path"]
        self.bootpar_path = os.path.join(
            game_dir,
            "main",
            "data",
            "bootpar",
            "boot_en.par",
        )
        self.wdrpar_path = os.path.join(
            game_dir,
            "main",
            "data",
            "wdr_par_en",
            "wdr.par",
        )

        asset_path = os.path.join("assets", "yakuza5")
        self.player_models = self._load_text(
            os.path.join(asset_path, "player_models.txt")
        )
        self.enemy_models = self._load_text(
            os.path.join(asset_path, "enemy_models.txt")
        )

    def randomize(self):
        self._randomize_player_models("boot_en")
        # self._randomize_enemy_models("wdr_par_en")

    def revert(self):
        print("Restoring player models")
        self._revert_file(self.bootpar_path)
        print("Restoring enemy models")
        self._revert_file(self.wdrpar_path)

    def _randomize_player_models(self):
        print("Randomizing player models")

        self._backup(self.bootpar_path)
        self._extract(self.bootpar_path)

        bin_name = "human_model.bin"
        bin_path = os.path.join(constants.TMP_DIR, "boot_en", bin_name)
        json_path = f"{bin_path}.json"
        new_bin_path = f"{json_path}.bin"
        subprocess.run([constants.EXPORTER, bin_path])

        model_data: Dict[str, Any]
        with open(json_path, encoding="utf-8") as f:
            model_data = json.load(f)

        for k, v in model_data.items():
            if k == "types":
                continue

            model: str = v.get("KIRYU_MODEL", "")
            if not model:
                continue

            new_model: str
            if model in self.changed_models:
                new_model = self.changed_models[model]
            else:
                new_model = random.choice(self.player_models)
                self.changed_models[model] = new_model

            v["KIRYU_MODEL"] = new_model

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(model_data, f, ensure_ascii=False, indent=4)

        subprocess.run([constants.IMPORTER, json_path])

        out_path = os.path.join(constants.OUT_DIR, "boot_en")
        os.makedirs(out_path, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(out_path, bin_name))

        out_par = os.path.join(constants.OUT_DIR, "boot_en.par")
        subprocess.run(
            [constants.PAR_TOOL, "add", self.bootpar_path, constants.OUT_DIR, out_par]
        )
        shutil.move(out_par, self.bootpar_path)

        shutil.rmtree(constants.TMP_DIR)
        shutil.rmtree(constants.OUT_DIR)

    def _randomize_enemy_models(self):
        print("Randomizing enemy models")

        self._backup(self.wdrpar_path)
        self._extract(self.wdrpar_path)

        par_dir_name = "wdr_en"
        bin_name = "dispose_string.bin"
        bin_path = os.path.join(constants.TMP_DIR, par_dir_name, bin_name)
        json_path = f"{bin_name}.json"
        new_bin_path = f"{json_path}.bin"
        dispose_string.forFile(bin_path)

        dispose_data: Dict[str, Any]
        with open(json_path) as f:
            dispose_data = json.load(f)

        count = dispose_data.get("NUMBER_ELEMENTS", 0)
        for i in range(count):
            k = str(i)
            model = dispose_data.get(k, "")
            if not model or not model.startswith("c_"):
                continue

            new_model: str
            if model in self.changed_models:
                new_model = self.changed_models[model]
            else:
                new_model = random.choice(self.enemy_models)
                self.changed_models[model] = new_model

            dispose_data[k] = new_model

        with open(json_path, "w") as f:
            json.dump(dispose_data, f, indent=2)

        dispose_string.forFile(json_path)

        out_path = os.path.join(constants.OUT_DIR, par_dir_name)
        os.makedirs(out_path, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(out_path, bin_name))

        out_par = os.path.join(constants.OUT_DIR, "wdr.par")
        subprocess.run(
            [constants.PAR_TOOL, "add", self.wdrpar_path, constants.OUT_DIR, out_par]
        )
        shutil.move(out_par, self.wdrpar_path)

        os.remove(json_path)
        shutil.rmtree(constants.TMP_DIR)
        shutil.rmtree(constants.OUT_DIR)
