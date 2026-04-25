# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

from ..utils import tqdm_download_util

from abc import abstractmethod, ABC
from urllib.parse import urljoin
from requests import request
from pathlib import Path
import configparser
import requests
import shutil
import json
import time
import re
import os


class BaseGameStrategy(ABC):
    """Base class for the game's unlock strategy."""
    def __init__(
        self,
        game_dir: Path = None,
        dlc_dir: Path = None,
        lib_path: Path = None
    ):
        self.game_dir = Path('.' if game_dir is None else game_dir)
        self.dlc_dir = Path(self.game_dir / "dlc" if dlc_dir is None else dlc_dir)
        self.lib_path = Path(self.game_dir if lib_path is None else lib_path)

    @property
    @abstractmethod
    def app_id(self) -> int: ...

    @property
    @abstractmethod
    def game_name(self) -> str: ...

    @property
    @abstractmethod
    def dlc_download_url(self) -> str: ...

    @property
    @abstractmethod
    def lib_download_url(self) -> str: ...

    @property
    @abstractmethod
    def dlc_files_validation_hashes(self) -> dict[str, str]: ...

    lib_filename: str = "libsteam_api.so"

    @abstractmethod
    def check_game_dir(self):
        pass

    def download_library(self) -> None:
        """Base library download method for github gde-fork"""
        try:
            asset_name = "emu-linux-release.tar.bz2"

            print("Downloading goldberg lib started...")
            res = requests.get(self.lib_download_url, timeout=15)
            res.raise_for_status()
            release_data = res.json()
            assets = release_data.get('assets', [])
            temp_dir = self.game_dir / 'temp'

            download_url = None
        
            for asset in assets:
                if asset['name'] == asset_name:
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                raise Exception(f"Error! File '{asset_name}' not found in latest release. "
                                f"Available files: {[a['name'] for a in assets]}")

            print(f"Downloading latest from: {download_url}")

            tqdm_download_util(download_url, temp_dir, asset_name)

            print("Extracting goldberg lib...")
            shutil.unpack_archive(temp_dir / asset_name, temp_dir)

            if os.path.exists(self.lib_path / self.lib_filename):
                shutil.move(self.lib_path / self.lib_filename, self.lib_path / (self.lib_filename+".bak"))

            shutil.move(temp_dir / f"release/regular/x64/{self.lib_filename}", str(self.lib_path))
            shutil.rmtree(temp_dir)
            print("Goldberg lib successfully installed!")

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Error! Cannot download goldberg lib. Check your network connection. {str(e)}")
        except Exception as e:
            raise Exception(f"Error during goldberg lib installation: {str(e)}")

    def get_dlcs_list(self) -> dict[str, str]:
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

        def clean_name(name) -> str:
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

    def create_configs(self, dlcs_list: dict[str, str]) -> None:
        print("Creating goldberg configs...")

        try:
            Path(self.game_dir / "steam_settings").mkdir(exist_ok=True, parents=True)

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

    def download_dlcs(self, data_to_download: list[str] = []) -> None:
        try:
            print("Downloading DLCs...")

            if not data_to_download:
                print("All DLCs is downloaded! Nothing to download. (use -f flag to reinstall DLCs)")
                return

            os.makedirs(self.dlc_dir, exist_ok=True)

            print(f"{len(data_to_download)} files to download. Starting download...")

            for file in data_to_download:
                filename = file+".zip"
                full_url = urljoin(self.dlc_download_url, filename)

                try:
                    tqdm_download_util(full_url, self.dlc_dir, filename)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        print(f"[ERROR!] Cannot find {filename} in file server!")
                    else:
                        raise e

            print("DLCs downloaded successfully!")

        except requests.exceptions.RequestException:
            raise requests.exceptions.RequestException("Error while downloading DLCs from main file server.\n"
                                                    f"Try to download files manually from ({self.dlc_download_url}).")
        except Exception:
            raise Exception("Unexpected error while downloading DLCs from main file server."
                            f"Try to download files manually from ({self.dlc_download_url})")