# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

from ..base_strategy import BaseGameStrategy
from .stellaris_hashes import dlc_hashes

from pathlib import Path
import requests
import os

class StellarisStrategy(BaseGameStrategy):

    app_id = 281990
    game_name = "Stellaris"
    lib_download_url = "https://api.github.com/repos/Detanup01/gbe_fork/releases/latest"
    dlc_download_url = "https://9924021b98ddcb42673ac2b9e55118bf.bckt.ru"
    dlc_files_validation_hashes = dlc_hashes

    def check_game_dir(self) -> None:
        try:
            if 'stellaris' not in os.listdir(self.game_dir):
                print(f"Cannot find 'stellaris' binary file in directory '{self.game_dir.absolute()}', are you sure this is correct path?")
                answer = input("Y/N?\n")
                if answer.lower() == "y" or answer.lower() == "yes":
                    pass
                elif answer.lower() == "n" or answer.lower() == "no":
                    print("Stopping. Please restart with right game directory path.")
                    print("Use 'ldu-tool install -p/--path <game_folder_path>' to indicate the path")
                    exit(1)
        except Exception:
            raise Exception("Unexpected error while checking game directory.")
