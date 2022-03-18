import argparse
import configparser
import random

from randomizer import Randomizer, Yakuza0Randomizer, Yakuza5Randomizer


def main():
    parser = argparse.ArgumentParser(description="Randomize a yakuza game")
    parser.add_argument(
        "game",
        help="specify which game to randomize",
        choices=("5", "0"),
    )
    parser.add_argument(
        "--revert",
        "-r",
        action="store_true",
        help="restore original backed up files",
    )
    parser.add_argument("--seed", "-s", help="specify a seed")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read("config.ini")

    rando: Randomizer
    if args.game == "5":
        rando = Yakuza5Randomizer(config)
    else:
        rando = Yakuza0Randomizer(config)

    if args.revert:
        rando.revert()
        return

    if args.seed:
        random.seed(args.seed)

    rando.randomize()


if __name__ == "__main__":
    main()
