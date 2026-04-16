#!/usr/bin/env python3

import requests
import os
import subprocess
import shutil
import argparse
from pathlib import Path 

class DLCTool():
    def __init__(self, game_dir):
        self.GITHUB_DATA_URL = 'https://raw.githubusercontent.com/seuyh/stellaris-dlc-unlocker/main/data.json'
        self.app_id=281990
        self.game_dir = Path('.' if game_dir is None else game_dir)
        self.dlc_dir = Path(self.game_dir / 'dlc/')

    def _check_game_dir(self):
        if 'stellaris' not in os.listdir(self.game_dir):
            print(f"Cannot find 'stellaris' binary file in directory '{self.game_dir.absolute()}', are you sure this is correct path?")
            answer = input("Input Y/N\n")
            if answer.lower() == "y" or answer.lower() == "yes":
                pass
            elif answer.lower() == "n" or answer.lower() == "no":
                print("Stopping. Please restart with right game directory path...")
                exit()

    def _download_goldberg_steamlib(self):
        print("Downloading goldberg lib...")
        res = requests.get("https://gitlab.com/Mr_Goldberg/goldberg_emulator/-/jobs/4247811310/artifacts/raw/linux/x86_64/libsteam_api.so?inline=false")
        with open(self.game_dir / "libsteam_api.so", "wb") as file:
            file.write(res.content)
        print("Goldberg lib successfully downloaded!")

    def _get_dlcs_list(self):
        print("Fetching DLCs list...")
        try:
            res = requests.get(f"https://api.steamcmd.net/v1/info/{self.app_id}", timeout=15)
        except requests.exceptions.ConnectionError:
            print("Error! Cannot reach https://api.steamcmd.net. Use VPN, if you from Russia.")
            exit()
        data = res.json()
        dlc_list_json = data['data'][str(self.app_id)]['extended']['listofdlc']
        dlc_list = dlc_list_json.split(',')
        print("DLCs list fetching done!")
        return dlc_list
    
    def _create_dlcs_file(self):
        try:
            print("Creating 'steam_settings' dir...")
            os.mkdir(self.game_dir / "steam_settings")
            print("'steam_settings' dir created!")
        except FileExistsError:
            pass
        except PermissionError:
            print("Error! Unable to create required folders in directory "
                  f"'{self.game_dir.absolute()}', please make sure you have all required permissions.")

        with open(self.game_dir / "steam_settings/dlc.txt", "+w") as txt_file:
            dlcs_list = self._get_dlcs_list()
            for id in dlcs_list:
                txt_file.write(f"{id}\n")

    def _get_dlcs_url(self):
        try:
            print("Fetching data from GitHub repo 'seuyh/stellaris-dlc-unlocker'...")
            res = requests.get(self.GITHUB_DATA_URL)
            urls = res.json()
            return urls
        except Exception as e:
            print("Error while fetching data form GitHub!\n")
            print(e)


    def _download_dlcs(self):
        urls = self._get_dlcs_url()
        try:
            print("Downloading DLCs...")
            subprocess.run(["bash", "-c", f"wget -P {self.dlc_dir} -r -l1 -H -nd -A zip {urls['url']}/unlocker/"])
            print("DLCs downloaded successfully!")
        except Exception as e:
            print(e)
            print("Error while downloading DLCs from main file server.")
            print(f"Try to download files manually from main server ({urls['url']}) or alternative ({urls['alturl']})")

    def _unzip_files(self):
        try:
            print("Unziping files...")
            for zip_file in os.listdir(self.dlc_dir):
                if zip_file.endswith(".zip"):
                    shutil.unpack_archive(self.dlc_dir / zip_file, self.dlc_dir)
                    os.remove(self.dlc_dir / zip_file)
            print("Files successfully unziped!")
        except Exception as e:
            print("Error during unpacking dlc archives!")
            print(e)

    def install_dlcs(self):
        print(f"DLCs installing started. Path {self.game_dir}")
        self._check_game_dir()
        self._download_dlcs()
        print("DLCs installing done!")

    def install_libs(self):
        print(f"Libs installing started. Path {self.game_dir}")
        self._check_game_dir()
        self._download_goldberg_steamlib()
        self._create_dlcs_file()
        print("Libs installing done!")

    def install(self):
        print(f"Installing started. Path {self.game_dir}")
        self._check_game_dir()
        self._download_goldberg_steamlib()
        self._create_dlcs_file()
        self._download_dlcs()
        self._unzip_files()
        print("Installing done! Launch the game? (only for Steam)")
        answer = input("Input Y/N\n")
        if answer.lower() == "y" or answer.lower() == "yes":
            try:
                subprocess.run(["bash", "-c", f"steam steam://run/{self.app_id}"])
                print("Launching...")
            except:
                print("Something went wrong... Oh come on! You can do it yourself! Don't be lazy!")
        elif answer.lower() == "n" or answer.lower() == "no":
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Linux DLC Unlocker Tool - unlocks all DLCs for Stellaris game.")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    install_parser = subparsers.add_parser("install", help="Install libs and DLCs")
    install_parser.add_argument("--dlc", action="store_true", help="Install DLCs")
    install_parser.add_argument("--libs", "-l", action="store_true", help="Install libs")
    install_parser.add_argument("--path", "-p", nargs=1, help="Install by specifying the path to the game.")

    args = parser.parse_args()

    if args.command == "install":
        game_path = args.path[0] if isinstance(args.path, list) else None

        dlc_tool = DLCTool(game_dir=game_path)

        if args.dlc:
            dlc_tool.install_dlcs()
        if args.libs:
            dlc_tool.install_libs()
        if not args.dlc and not args.libs:
            dlc_tool.install()
    else:
        parser.print_help()