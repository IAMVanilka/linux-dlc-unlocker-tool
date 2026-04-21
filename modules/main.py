#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

from .configs.dlc_folders_hashes import dlc_hashes
from ._version import __version__
from dirhash import dirhash
from pathlib import Path 
from urllib.parse import urljoin
from tqdm import tqdm
import configparser
import subprocess
import requests
import argparse
import json
import time
import shutil
import os
import re


APP_ID = 281990
GITHUB_DATA_FILE_URL = 'https://raw.githubusercontent.com/seuyh/stellaris-dlc-unlocker/main/data.json'
GITHUB_GBE_URL = "https://api.github.com/repos/Detanup01/gbe_fork/releases/latest"
ASSET_NAME = "emu-linux-release.tar.bz2"

class DLCTool:
    def __init__(self, game_dir: str | Path = None):
        self.github_data_file_url: str = GITHUB_DATA_FILE_URL
        self.github_gbe_url: str = GITHUB_GBE_URL
        self.asset_name: str = ASSET_NAME
        self.app_id = APP_ID
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
        
    def hash_check(self) -> list[str]:
        print("DLC files checking...")
        dlcs_to_download = []

        Path(self.dlc_dir).mkdir(exist_ok=True)

        local_dlc_folders = os.scandir(self.dlc_dir)
        local_dlc_folders = {dlc_folder.name:dlc_folder.path for dlc_folder in local_dlc_folders}

        for dlc, dlc_hash in dlc_hashes.items():
            if dlc in local_dlc_folders:
                local_dlc_path = local_dlc_folders[dlc]
                local_dlc_hash = dirhash(local_dlc_path, "md5")
                if local_dlc_hash != dlc_hash:
                    dlcs_to_download.append(dlc)
                    continue
            else:
                dlcs_to_download.append(dlc)
                continue
        
        if dlcs_to_download:
            print(f"List of DLCs for download: {dlcs_to_download}")
        else:
            print("Nothing to download.")

        return dlcs_to_download

    def _download_goldberg_steamlib(self):
        try:
            print("Downloading goldberg lib started...")
            res = requests.get(self.github_gbe_url, timeout=15)
            res.raise_for_status()
            release_data = res.json()
            assets = release_data.get('assets', [])
            temp_dir = self.game_dir / 'temp'

            download_url = None
            
            for asset in assets:
                if asset['name'] == self.asset_name:
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                raise Exception(f"Error! File '{self.asset_name}' not found in latest release. "
                              f"Available files: {[a['name'] for a in assets]}")

            print(f"Downloading latest from: {download_url}")

            with requests.get(download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                        
                total_size = int(r.headers.get('content-length', 0))
                
                Path(temp_dir).mkdir(exist_ok=True)
                temp_file = temp_dir / self.asset_name
                
                with open(temp_file, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc='goldberg lib') as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))

            print("Extracting goldberg lib...")
            shutil.unpack_archive(str(temp_file), temp_dir)
            shutil.move(temp_dir / "release/regular/x64/libsteam_api.so", str(self.game_dir / "libsteam_api.so"))
            shutil.rmtree(temp_dir)
            print("Goldberg lib successfully installed!")
            
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Error! Cannot download goldberg lib. Check your network connection. {str(e)}")
        except Exception as e:
            raise Exception(f"Error during goldberg lib installation: {str(e)}")

    def _get_dlcs_list(self):
        print("Fetching DLCs list...")
        cache_dir = Path.home() / '.cache' / 'steamcmd_dlc'
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f'{self.app_id}.json'
        cache_ttl = 1800

        data = None
        if cache_file.exists() and (time.time() - os.path.getmtime(cache_file)) < cache_ttl:
            with open(cache_file, 'r') as f:
                data = json.load(f)
        else:
            try:
                res = requests.get(f"https://api.steamcmd.net/v1/info/{self.app_id}", timeout=15)
                res.raise_for_status()
                data = res.json()
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
            except requests.exceptions.ConnectionError as e:
                raise requests.exceptions.ConnectionError(
                    "Error! Cannot connect to api.steamcmd.net. "
                    "This endpoint may be blocked in Russia. "
                    "Please check your network connection or use a VPN. "
                    f"{e}"
                )
            except requests.exceptions.Timeout as e:
                raise requests.exceptions.Timeout(
                    "Timeout while connecting to api.steamcmd.net. "
                    "This endpoint may be blocked or unreachable from your location. "
                    f"{e}"
                )
            except requests.exceptions.HTTPError:
                raise
            except requests.exceptions.RequestException as e:
                raise requests.exceptions.RequestException(
                    "Error while fetching DLC metadata from api.steamcmd.net. "
                    "This endpoint may be unavailable or blocked in your region. "
                    f"{e}"
                )

        if 'data' not in data or str(self.app_id) not in data['data']:
            raise Exception("No data found")

        app_data = data['data'][str(self.app_id)]
        dlc_dict = {}

        def clean_name(name):
            # Убираем "Stellaris:" или "Stellaris" в начале (с любыми вариантами пробелов)
            name = re.sub(r'^[ \t]*Stellaris[ \t]*[:-][ \t]*', '', name, flags=re.IGNORECASE)
            name = re.sub(r'^[ \t]*Stellaris[ \t]+', '', name, flags=re.IGNORECASE)
            # Убираем оставшиеся переносы строк и лишние пробелы по краям
            name = name.strip()
            return name

        dlc_list_str = app_data.get('extended', {}).get('listofdlc')
        if dlc_list_str:
            dlc_ids = [id.strip() for id in dlc_list_str.split(',') if id.strip()]
            for dlc_id in dlc_ids:
                dlc_name = app_data.get('dlc', {}).get(dlc_id, {}).get('name')
                if not dlc_name:
                    dlc_cache = cache_dir / f'{dlc_id}.json'
                    if not dlc_cache.exists() or (time.time() - os.path.getmtime(dlc_cache)) >= cache_ttl:
                        shutil.rmtree(cache_dir / f'{dlc_id}.json', ignore_errors=True)
                        try:
                            res = requests.get(f"https://api.steamcmd.net/v1/info/{dlc_id}", timeout=15)
                            res.raise_for_status()
                            dlc_data = res.json()
                            with open(dlc_cache, 'w') as f:
                                json.dump(dlc_data, f)
                        except:
                            pass
                    if dlc_cache.exists():
                        with open(dlc_cache, 'r') as f:
                            dlc_data = json.load(f)
                        dlc_name = dlc_data.get('data', {}).get(str(dlc_id), {}).get('common', {}).get('name', f'DLC_{dlc_id}')
                    else:
                        dlc_name = f'DLC_{dlc_id}'
                dlc_dict[dlc_id] = clean_name(dlc_name)
        else:
            dlc_obj = app_data.get('dlc', {})
            for key, value in dlc_obj.items():
                if key.isdigit():
                    dlc_name = value.get('name', f'DLC_{key}')
                    dlc_dict[key] = clean_name(dlc_name)

        print("DLCs list fetching done!")
        return dlc_dict
    
    def _create_goldberg_configs(self):
        print("Creating goldberg configs...")

        try:
            Path(self.game_dir / "steam_settings").mkdir(exist_ok=True, parents=True)

            dlcs_list = self._get_dlcs_list()

            config = configparser.ConfigParser()
            config.add_section('app::dlcs')
            for key, value in dlcs_list.items():
                config.set('app::dlcs', key, value)
            config.add_section('app::cloud_save::general')
            config.set('app::cloud_save::general', 'create_default_dir', '1')

            with open(self.game_dir / "steam_settings/configs.app.ini", 'w') as configfile:
                config.write(configfile)
            with open(self.game_dir / "steam_settings/steam_appid.txt", 'w') as txt_file:
                txt_file.write(f"{self.app_id}")      

            print("Creating goldberg configs done!")
        except Exception as e:
            raise Exception(f"Error creating goldberg configs: {e}")  

    def _get_dlcs_url(self):
        try:
            print("Fetching data from GitHub repo 'seuyh/stellaris-dlc-unlocker'...")
            res = requests.get(self.github_data_file_url)
            if res.status_code == 200:
                urls = res.json()
                return urls
            else:
                print(f"Error! GitHub returns {res.status_code} status code!")
                return None
        except requests.exceptions.ConnectionError:
            raise(requests.exceptions.ConnectionError("Error! Cannot connect to gitlab.com. Check your network connection."))
        except Exception:
            raise Exception("Error while fetching data form GitHub!")

    def _download_dlcs(self, data_to_download: list[str] = [], force = False):
        if not data_to_download and not force:
            return

        urls = self._get_dlcs_url()
        if urls is None:
            raise Exception("Failed to fetch URLs from GitHub")
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
                if Path(filename).with_suffix('').name in data_to_download or force:
                    print("LOADING FILE: ", filename)
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
                else:
                    continue

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

    def install_dlcs(self, force = False):
        print(f"DLCs installing started{" [FORCED]." if force else "."} Path: {self.game_dir.absolute()}")
        if not force:
            files_to_download = self.hash_check()
            self._download_dlcs(files_to_download)
        else:
            self._download_dlcs(force=force)

        self._unzip_files()
        print("DLCs installing done!")

    def install_libs(self):
        print(f"Libs installing started. Path: {self.game_dir.absolute()}")
        self._download_goldberg_steamlib()
        self._create_goldberg_configs()
        print("Libs installing done!")

    def install(self, force = False):
        print(f"Installing started{" [FORCED]." if force else "."}. Path: {self.game_dir.absolute()}")
        self._download_goldberg_steamlib()
        self._create_goldberg_configs()

        if not force:
            files_to_download = self.hash_check()
            self._download_dlcs(files_to_download)
        else:
            self._download_dlcs(force=force)

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
                print("Input y/yes or n/no")


def run():
    parser = argparse.ArgumentParser(description="Linux DLC Unlocker Tool - unlocks all DLCs for Stellaris game.")

    parser.add_argument("-V", "--version", action="store_true", help="Print current version")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    install_parser = subparsers.add_parser("install", help="Install libs and DLCs")
    install_parser.add_argument("--dlc", action="store_true", help="Install DLCs")
    install_parser.add_argument("-l", "--libs", action="store_true", help="Install libs")
    install_parser.add_argument("-p", "--path", nargs=1, help="Install by specifying the path to the game.")
    install_parser.add_argument("-f", "--force", action="store_true", help="Reinstall all DLCs even if they have already been downloaded.")

    args = parser.parse_args()
    
    if args.version:
        print(f"Linux DLC Unlocker Tool v.{__version__}")
    elif args.command == "install":
        game_path = args.path[0] if isinstance(args.path, list) else None

        dlc_tool = DLCTool(game_dir=game_path)
        dlc_tool.check_game_dir()

        FORCE_FLAG = True if args.force else False

        if args.dlc:
            dlc_tool.install_dlcs(force=FORCE_FLAG)
        if args.libs:
            dlc_tool.install_libs()
        if not args.dlc and not args.libs:
            dlc_tool.install(force=FORCE_FLAG)
    else:
        parser.print_help()
