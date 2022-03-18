# yakuzarando

## Prereqs

1. Python 3
2. Par Tool: https://github.com/Kaplas80/ParManager/releases/tag/v1.3.3
3. 2007.03.19 .bin file editor: https://github.com/SlowpokeVG/Yakuza-2007.03.19-bin-file-exporter-importer/releases/tag/1.42

Place the `.exe`s for par tool and the bin editor in this folder (beside `main.py`).

## Usage

Edit `config.ini` to specify your Yakuza 5 directory, then just run `python main.py`. The rando will create a backup of the changed `.par` file in your game directory.

```
usage: main.py [-h] [--revert] [--seed SEED]

Randomize a yakuza game

optional arguments:
  -h, --help            show this help message and exit
  --revert, -r          restore original backed up files
  --seed SEED, -s SEED  specify a seed
```

## Support

### Games

- Yakuza 5

### Features

- Player character models
