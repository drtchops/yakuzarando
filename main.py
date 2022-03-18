import argparse
import configparser
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pydoc import describe
from typing import Any, Dict

from dispose_string import forFile

PAR_TOOL = "ParTool.exe"
EXPORTER = "20070319exporter-win.exe"
EXPORTER_CP932 = "20070319exporterCP932-win.exe"
IMPORTER = "20070319importer-win.exe"
IMPORTER_CP932 = "20070319importerCP932.exe"
TMP_DIR = "tmp"
OUT_DIR = "out"


class Randomizer:
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        with open("player_models.txt") as f:
            self.player_models = [
                m.strip() for m in f.readlines() if m and not m.startswith("#")
            ]

        with open("enemy_models.txt") as f:
            self.enemy_models = [
                m.strip() for m in f.readlines() if m and not m.startswith("#")
            ]

        self.changed_models: Dict[str, str] = {}

    def update_boot_par(self, par_name: str):
        print("Randomizing player models")

        y5_dir = self.config["General"]["Yakuza5Path"]
        bin_name = "human_model.bin"
        par_path = os.path.join(y5_dir, "main", "data", "bootpar", f"{par_name}.par")
        bak_path = f"{par_path}.bak"
        if os.path.exists(bak_path):
            shutil.copyfile(bak_path, par_path)
        else:
            shutil.copyfile(par_path, bak_path)

        subprocess.run([PAR_TOOL, "extract", par_path, TMP_DIR])

        bin_path = os.path.join(TMP_DIR, par_name, bin_name)
        json_path = f"{bin_path}.json"
        new_bin_path = f"{json_path}.bin"
        exporter = EXPORTER_CP932 if par_name == "boot" else EXPORTER
        subprocess.run([exporter, bin_path])

        model_data: Dict[str, Any]
        with open(json_path, encoding="utf-8") as f:
            model_data = json.load(f)

        model_key = "桐生の姿" if par_name == "boot" else "KIRYU_MODEL"

        for k, v in model_data.items():
            if k == "types":
                continue

            model: str = v.get(model_key, "")
            if not model:
                continue

            new_model: str
            if model in self.changed_models:
                new_model = self.changed_models[model]
            else:
                new_model = random.choice(self.player_models)
                self.changed_models[model] = new_model

            v[model_key] = new_model

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(model_data, f, ensure_ascii=False, indent=4)

        importer = IMPORTER_CP932 if par_name == "boot" else IMPORTER
        subprocess.run([importer, json_path])

        out_path = os.path.join(OUT_DIR, par_name)
        os.makedirs(out_path, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(out_path, bin_name))

        out_par = os.path.join(OUT_DIR, f"{par_name}.par")
        subprocess.run([PAR_TOOL, "add", par_path, OUT_DIR, out_par])
        shutil.move(out_par, par_path)

        shutil.rmtree(TMP_DIR)
        shutil.rmtree(OUT_DIR)

    def update_wdr_par(self, par_name: str):
        print("Randomizing enemy models")

        y5_dir = self.config["General"]["Yakuza5Path"]
        par_path = os.path.join(y5_dir, "main", "data", par_name, "wdr.par")
        bak_path = f"{par_path}.bak"
        if os.path.exists(bak_path):
            shutil.copyfile(bak_path, par_path)
        else:
            shutil.copyfile(par_path, bak_path)

        subprocess.run([PAR_TOOL, "extract", par_path, TMP_DIR])

        par_dir_name = par_name.replace("_par", "")
        bin_name = "dispose_string.bin"
        bin_path = os.path.join(TMP_DIR, par_dir_name, bin_name)
        json_path = f"{bin_name}.json"
        new_bin_path = f"{json_path}.bin"
        forFile(bin_path)

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

        forFile(json_path)

        out_path = os.path.join(OUT_DIR, par_dir_name)
        os.makedirs(out_path, exist_ok=True)
        shutil.move(new_bin_path, os.path.join(out_path, bin_name))

        out_par = os.path.join(OUT_DIR, "wdr.par")
        subprocess.run([PAR_TOOL, "add", par_path, OUT_DIR, out_par])
        shutil.move(out_par, par_path)

        os.remove(json_path)
        shutil.rmtree(TMP_DIR)
        shutil.rmtree(OUT_DIR)

    def randomize(self):
        self.update_boot_par("boot_en")
        # self.update_wdr_par("wdr_par_en")

    def revert(self):
        y5_dir = self.config["General"]["Yakuza5Path"]

        bootpar_path = os.path.join(y5_dir, "main", "data", "bootpar", "boot_en.par")
        bootpar_bak_path = f"{bootpar_path}.bak"
        if os.path.exists(bootpar_bak_path):
            print("Restoring player models")
            shutil.copyfile(bootpar_bak_path, bootpar_path)

        wdr_par_path = os.path.join(y5_dir, "main", "data", "wdr_par_en", "wdr.par")
        wdr_bak_path = f"{wdr_par_path}.bak"
        if os.path.exists(wdr_bak_path):
            print("Restoring enemy models")
            shutil.copyfile(wdr_bak_path, wdr_par_path)


def main():
    parser = argparse.ArgumentParser(description="Randomize a yakuza game")
    parser.add_argument(
        "--revert",
        "-r",
        action="store_true",
        help="restore original backed up files",
    )
    parser.add_argument("--seed", "-s", help="specify a seed")
    args = parser.parse_args()

    rando = Randomizer()

    if args.revert:
        rando.revert()
        return
    if args.seed:
        random.seed(args.seed)

    rando.randomize()


if __name__ == "__main__":
    main()
