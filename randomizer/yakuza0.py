import json
import os
import random
import re
import shutil
import subprocess
from configparser import ConfigParser
from typing import Any, Dict

from utils import constants, dispose_string

from .randomizer import Game, Randomizer


class Yakuza0Randomizer(Randomizer):
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config, Game.Yakuza0)
        game_dir = self.config["General"]["Yakuza0Path"]
        self.bootpar_path = os.path.join(
            game_dir,
            "media",
            "data",
            "bootpar",
            "boot.par",
        )
        self.wdrpar_path = os.path.join(
            game_dir,
            "media",
            "data",
            "wdr_par_c",
            "wdr.par",
        )
        self.exe_path = os.path.join(game_dir, "media", "Yakuza0.exe")

        asset_path = os.path.join("assets", "yakuza0")
        self.models = self._load_text(os.path.join(asset_path, "models.txt"))
        self.styles = self._load_text(os.path.join(asset_path, "styles.txt"))

    def randomize(self):
        self._randomize_player_models()
        self._randomize_npc_models()
        self._randomize_player_movesets()
        # self._randomize_enemy_movesets()

    def revert(self):
        print("Restoring player models")
        self._revert_file(self.bootpar_path)
        print("Restoring NPC models")
        self._revert_file(self.wdrpar_path)
        print("Restoring player movesets")
        self._revert_file(self.exe_path)

    def _randomize_player_models(self):
        print("Randomizing player models")

        self._backup(self.bootpar_path)
        self._extract(self.bootpar_path)

        bin_name = "human_model.bin_c"
        bin_path = os.path.join(constants.TMP_DIR, bin_name)
        json_path = f"{bin_path}.json"
        new_bin_path = f"{json_path}.bin"
        subprocess.run([constants.EXPORTER, bin_path])

        model_data: Dict[str, dict]
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
                new_model = random.choice(self.models)
                self.changed_models[model] = new_model

            v["KIRYU_MODEL"] = new_model

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(model_data, f, ensure_ascii=False, indent=4)

        subprocess.run([constants.IMPORTER, json_path])

        os.makedirs(constants.OUT_DIR, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(constants.OUT_DIR, bin_name))

        out_par = os.path.join(constants.OUT_DIR, "boot.par")
        subprocess.run(
            [constants.PAR_TOOL, "add", self.bootpar_path, constants.OUT_DIR, out_par]
        )
        shutil.move(out_par, self.bootpar_path)

        shutil.rmtree(constants.TMP_DIR)
        shutil.rmtree(constants.OUT_DIR)

    def _randomize_npc_models(self):
        print("Randomizing NPC models")

        self._backup(self.wdrpar_path)
        self._extract(self.wdrpar_path)

        bin_name = "dispose_string.bin"
        bin_path = os.path.join(constants.TMP_DIR, bin_name)
        json_path = f"{bin_name}.json"
        new_bin_path = f"{json_path}.bin"
        dispose_string.forFile(bin_path)

        dispose_data: Dict[str, Any]
        with open(json_path) as f:
            dispose_data = json.load(f)

        names = (
            "Tapioca",
            "Froob",
            "Chops",
            "Ichiban",
            "Kiwami",
        )

        count = dispose_data.get("NUMBER_ELEMENTS", 0)
        for i in range(count):
            k = str(i)
            v = dispose_data.get(k, "")

            if not v:
                continue

            if v.startswith("c_"):
                new_model: str
                if v in self.changed_models:
                    new_model = self.changed_models[v]
                else:
                    new_model = random.choice(self.models)
                    self.changed_models[v] = new_model

                dispose_data[k] = new_model
                continue

            if re.match(r"^[A-Z][a-z]+( [A-Z][a-z]+)*$", v) and 722 < i < 737:
                # TODO: figure out which of these don't crash
                new_name = random.choice(names)
                dispose_data[k] = f"{new_name} {k}"

        with open(json_path, "w") as f:
            json.dump(dispose_data, f, indent=2)

        dispose_string.forFile(json_path)

        os.makedirs(constants.OUT_DIR, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(constants.OUT_DIR, bin_name))

        out_par = os.path.join(constants.OUT_DIR, "wdr.par")
        subprocess.run(
            [constants.PAR_TOOL, "add", self.wdrpar_path, constants.OUT_DIR, out_par]
        )
        shutil.move(out_par, self.wdrpar_path)

        os.remove(json_path)
        shutil.rmtree(constants.TMP_DIR)
        shutil.rmtree(constants.OUT_DIR)

    def _randomize_player_movesets(self):
        print("Randomizing player movesets")

        self._backup(self.exe_path)

        styles = [
            bytes(s, "utf-8").ljust(16, b"\0") for s in self.styles if len(s) < 16
        ]
        player_styles = (
            b"p_kiryu_s\0\0\0\0\0\0\0",
            b"p_kiryu_h\0\0\0\0\0\0\0",
            b"p_kiryu_c\0\0\0\0\0\0\0",
            b"p_kiryu_l\0\0\0\0\0\0\0",
            b"p_majima_a\0\0\0\0\0\0",
            b"p_majima_d\0\0\0\0\0\0",
            b"p_majima_b\0\0\0\0\0\0",
            b"p_majima_l\0\0\0\0\0\0",
        )

        exe_data: bytes
        with open(self.exe_path, "rb") as f:
            exe_data = f.read()

        for p in player_styles:
            new_style = random.choice(styles)
            exe_data = exe_data.replace(p, new_style, 1)

        with open(self.exe_path, "wb") as f:
            f.write(exe_data)

    def _randomize_enemy_movesets(self):
        print("Randomizing enemy movesets")

        self._backup(self.bootpar_path)
        self._extract(self.bootpar_path)

        bin_name = "enemy_ai_param.bin"
        # TODO
