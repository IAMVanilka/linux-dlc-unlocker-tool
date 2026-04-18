#!/usr/bin/env python3

from modules._version import __version__
from urllib.parse import urljoin
from pathlib import Path 
from tqdm import tqdm
import subprocess
import requests
import argparse
import shutil
import os
import re


APP_ID = 281990

class DLCTool:
    def __init__(self, game_dir):
        self.GITHUB_DATA_URL = 'https://raw.githubusercontent.com/seuyh/stellaris-dlc-unlocker/main/data.json'
        self.app_id=APP_ID
        self.game_dir = Path('.' if game_dir is None else game_dir)
        self.dlc_dir = Path(self.game_dir / 'dlc/')

    def check_game_dir(self):
        try:
            if 'stellaris' not in os.listdir(self.game_dir):
                print(f"Cannot find 'stellaris' binary file in directory '{self.game_dir.absolute()}', are you sure this is correct path?")
                answer = input("Y/N?\n")
                if answer.lower() == "y" or answer.lower() == "yes":
                    pass
                elif answer.lower() == "n" or answer.lower() == "no":
                    print("Stopping. Please restart with right game directory path...")
                    exit(1)
        except Exception:
            raise Exception("Unexpected error while checking game directory.")

    def _download_goldberg_steamlib(self):
        print("Downloading goldberg lib...")
        try:
            res = requests.get("https://gitlab.com/Mr_Goldberg/goldberg_emulator/-/jobs/4247811310/artifacts/raw/linux/x86_64/libsteam_api.so?inline=false", timeout=15)
            if res.status_code == 200:
                with open(self.game_dir / "libsteam_api.so", "wb") as file:
                    file.write(res.content)
                print("Goldberg lib successfully downloaded!")
            else:
                print(f"Error! GitLab returns {res.status_code} status code!")
        except requests.exceptions.ConnectionError:
            raise(requests.exceptions.ConnectionError("Error! Cannot connect to gitlab.com. Check your network connection."))

    def _get_dlcs_list(self):
        print("Fetching DLCs list...")
        try:
            res = requests.get(f"https://api.steamcmd.net/v1/info/{self.app_id}", timeout=15)
            if res.status_code == 200:
                data = res.json()
                dlc_list_json = data['data'][str(self.app_id)]['extended']['listofdlc']
                dlc_list = dlc_list_json.split(',')
                print("DLCs list fetching done!")
                return dlc_list
            else:
                print(f"Error! steamcmd.net returns {res.status_code} status code!")
        except requests.exceptions.ConnectionError:
            raise(requests.exceptions.ConnectionError("Error! Cannot reach https://api.steamcmd.net. Use VPN, if you from Russia."))
        except Exception:
            raise(Exception("Error while trying to get dlcs list!"))
    
    def _create_dlcs_file(self):
        try:
            print("Creating 'steam_settings' dir...")
            os.mkdir(self.game_dir / "steam_settings")
            print("'steam_settings' dir created!")

            with open(self.game_dir / "steam_settings/dlc.txt", "+w") as txt_file:
                dlcs_list = self._get_dlcs_list()
                for id in dlcs_list:
                    txt_file.write(f"{id}\n")
        except FileExistsError:
            pass
        except PermissionError:
            print("Error! Unable to create required folders in directory "
                  f"'{self.game_dir.absolute()}', please make sure you have all required permissions.")
        except Exception:
            raise Exception("Unexpected error while creating dlc.txt file.")

    def _get_dlcs_url(self):
        try:
            print("Fetching data from GitHub repo 'seuyh/stellaris-dlc-unlocker'...")
            res = requests.get(self.GITHUB_DATA_URL)
            if res.status_code == 200:
                urls = res.json()
                return urls
            else:
                print(f"Error! GitHub returns {res.status_code} status code!")
        except requests.exceptions.ConnectionError:
            raise(requests.exceptions.ConnectionError("Error! Cannot connect to gitlab.com. Check your network connection."))
        except Exception:
            raise Exception("Error while fetching data form GitHub!")

    def _download_dlcs(self):
        urls = self._get_dlcs_url()
        base_url = f"https://{urls['url']}/unlocker/"
        try:
            print("Downloading DLCs...")
            os.makedirs(self.dlc_dir, exist_ok=True)

            response = requests.get(base_url, timeout=30)
            response.raise_for_status()

            zip_links = re.findall(r'<a\s+[^>]*href=["\']([^"\']*\.zip[^"\']*)["\']', response.text)

            if not zip_links:
                print("Error! Cannot find '.zip' files in the server")
                return

            print(f"Founded files: {len(zip_links)}. Starting download...")
            
            for link in zip_links:
                full_url = urljoin(base_url, link)
                filename = Path(full_url.split('?')[0]).name
                filepath = self.dlc_dir / filename

                with requests.get(full_url, stream=True, timeout=60) as file_res:
                    file_res.raise_for_status()
                    total_size = int(file_res.headers.get('content-length', 0))

                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                        with open(filepath, 'wb') as f:
                            for chunk in file_res.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))

                print(f"Done: {filename}")

            print("DLCs downloaded successfully!")

        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Error while downloading DLCs from main file server.\n"
                                                       f"Try to download files manually from main server ({urls['url']}) or alternative ({urls['alturl']})")
        except Exception:
            raise Exception("Unexpected error while downloading DLCs from main file server."
                            f"Try to download files manually from main server ({urls['url']}) or alternative ({urls['alturl']})")

    def _unzip_files(self):
        try:
            print("Unziping files...")
            for zip_file in os.listdir(self.dlc_dir):
                if zip_file.endswith(".zip"):
                    shutil.unpack_archive(self.dlc_dir / zip_file, self.dlc_dir)
                    os.remove(self.dlc_dir / zip_file)
            print("Files successfully unziped!")
        except Exception:
            raise Exception("Error during unpacking dlc archives!")

    def install_dlcs(self):
        print(f"DLCs installing started. Path {self.game_dir}")
        self._download_dlcs()
        print("DLCs installing done!")

    def install_libs(self):
        print(f"Libs installing started. Path {self.game_dir}")
        self._download_goldberg_steamlib()
        self._create_dlcs_file()
        print("Libs installing done!")

    def install(self):
        print(f"Installing started. Path {self.game_dir}")
        self._download_goldberg_steamlib()
        self._create_dlcs_file()
        self._download_dlcs()
        self._unzip_files()
        print("Installing done! Launch the game? (only for Steam)")
        while True:
            answer = input("Y/N?\n")
            if answer.lower() == "y" or answer.lower() == "yes":
                try:
                    subprocess.run(["bash", "-c", f"steam steam://run/{self.app_id} &"])
                    print("Launching...")
                    break
                except:
                    print("Something went wrong... Oh come on! You can do it yourself! Don't be lazy!")
                    break
            elif answer.lower() == "n" or answer.lower() == "no":
                break
            else:
                print("Input y/yes or n/no\n")


def run():
    parser = argparse.ArgumentParser(description="Linux DLC Unlocker Tool - unlocks all DLCs for Stellaris game.")

    parser.add_argument("-V", "--version", action="store_true", help="Print current version")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    install_parser = subparsers.add_parser("install", help="Install libs and DLCs")
    install_parser.add_argument("--dlc", action="store_true", help="Install DLCs")
    install_parser.add_argument("-l", "--libs", action="store_true", help="Install libs")
    install_parser.add_argument("-p", "--path", nargs=1, help="Install by specifying the path to the game.")

    args = parser.parse_args()
    
    if args.version:
        print(f"Linux DLC Unlocker Tool v. {__version__}")
    elif args.command == "install":
        game_path = args.path[0] if isinstance(args.path, list) else None

        dlc_tool = DLCTool(game_dir=game_path)
        dlc_tool.check_game_dir()

        if args.dlc:
            dlc_tool.install_dlcs()
        if args.libs:
            dlc_tool.install_libs()
        if not args.dlc and not args.libs:
            dlc_tool.install()
    else:
        parser.print_help()
