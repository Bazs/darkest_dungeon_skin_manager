import argparse
import json
import os
from pathlib import Path

from gui import start_gui
from master_manifest import MasterManfiest


def validate_command_line_arguments(arguments):
    if not arguments.game_steam_folder.is_dir():
        raise FileNotFoundError(arguments.game_steam_folder)
    if not os.path.isdir(arguments.manager_folder):
        raise FileNotFoundError(arguments.manager_folder)


def parse_configuration():
    configuration_file_relative_path = Path("configuration.json")
    assert Path.is_file(configuration_file_relative_path), "Could not find configuration.json"
    with open(configuration_file_relative_path) as config_file:
        configuration = json.load(config_file)
        return configuration


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("-g", "--game_steam_folder",
                                 help="The steamapps folder where Darkest Dungeon is installed", required=True,
                                 type=Path)
    argument_parser.add_argument("-m", "--manager_folder", help="The folder where the skin manager will store the skins"
                                                                "and intermediate files. Don't manually edit the "
                                                                "contents within, and keep this argument constant "
                                                                "across multiple invocations", required=True, type=Path)
    arguments = argument_parser.parse_args()
    validate_command_line_arguments(arguments)
    configuration = parse_configuration()

    start_gui(configuration=configuration, mod_manager_folder=arguments.manager_folder,
              game_folder=arguments.game_steam_folder)
