# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

import os
import shutil
import requests
import subprocess
from pathlib import Path
from shutil import ReadError

from tqdm import tqdm
from dirhash import dirhash

def tqdm_download_util(from_url: str, to_dir: str | Path, filename: str) -> None:
    with requests.get(from_url, stream=True, timeout=30) as res:
        res.raise_for_status()
                
        total_size = int(res.headers.get('content-length', 0))
        
        Path(to_dir).mkdir(exist_ok=True, parents=True)
        file_to_download = to_dir / filename
        
        with open(file_to_download, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

def files_hash_check(folder_to_check: str | Path, dlc_hashes: dict[str, str]) -> list[str]:
    print("DLC files checking...")
    dlcs_to_download = []

    Path(folder_to_check).mkdir(exist_ok=True)

    local_dlc_folders = os.scandir(folder_to_check)
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

def unzip_files(dir_to_unzip: Path) -> None:
    try:
        print("Unziping files...")
        Path(dir_to_unzip).mkdir(exist_ok=True, parents=True)
        for zip_file in os.listdir(dir_to_unzip):

            try:
                if zip_file.endswith(".zip"):
                    shutil.unpack_archive(dir_to_unzip / zip_file, dir_to_unzip)
                    os.remove(dir_to_unzip / zip_file)
            except ReadError:
                print(f"[ERROR!] Can't read {zip_file} file!")

        print("Files successfully unziped!")
    except Exception:
        raise Exception("Error during unpacking dlc archives!")

def run_the_game(app_id: int):
    try:
        subprocess.run(["bash", "-c", f"steam steam://run/{app_id} &"])
        print("Launching...")
    except:
        print("Something went wrong... Oh come on! You can do it yourself! Don't be lazy!")

def hash_generator(path_to_folder: str | Path, hashes_filename: str):
    hashes_dict = {}
    for folder in os.scandir(path_to_folder):
        folder_hash = dirhash(folder.path, "md5")
        hashes_dict[folder.name] = folder_hash

    if not hashes_filename.endswith(".py"):
        hashes_filename = f"{hashes_filename}.py"

    with open(hashes_filename, "w", encoding="utf-8") as hashes_file:
        lines = ["dlc_hashes: dict[str, str] = {"]
        
        for key, value in hashes_dict.items():
            lines.append(f'    "{key}": "{value}",')
            
        lines.append("}")

        hashes_file.write("\n".join(lines) + "\n")

    print(f"Hashes file created!")
