# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

import subprocess
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

def mount_steam_workshop(game_dir: str | Path, app_id: int | str):
    def _ensure_sudo():
        if os.geteuid() != 0:
            print("⚠️ Superuser privileges are required for mounting.")
            try:
                subprocess.run(["sudo", "-v"], check=True, capture_output=True)
                print("✅ Sudo privileges successfully acquired.")
            except subprocess.CalledProcessError:
                raise PermissionError("Failed to obtain sudo privileges. Please run the script with: sudo python3 your_script.py")

    _ensure_sudo()

    game_dir = Path(game_dir)
    mods_dir = game_dir.absolute() / "steam_settings/mods"
    workshop_dir = game_dir.absolute().parent.parent / "workshop/content" / str(app_id)

    mods_dir.mkdir(parents=True, exist_ok=True)
    workshop_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Game mods directory: {mods_dir}")
    print(f"📂 Steam Workshop content directory: {workshop_dir}")
    print("⏳ Mounting Steam Workshop content...")

    try:
        subprocess.run(
            ["sudo", "mount", "--bind", str(workshop_dir), str(mods_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Mount successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during mounting:\n{e.stderr.strip()}")
        return

    user_answer = input("Add this mount point to /etc/fstab for automatic mounting after reboot? (Y/N): ").strip().lower()

    if user_answer == "y":
        print("💾 Adding entry to fstab...")
        fstab_entry = f"{workshop_dir} {mods_dir} none bind 0 0\n"
        try:
            subprocess.run(
                ["sudo", "tee", "-a", "/etc/fstab"],
                input=fstab_entry,
                text=True,
                check=True,
                capture_output=True
            )

            subprocess.run(["sudo", "mount", "-a"], check=True, capture_output=True)
            print("✅ Entry added to fstab and applied successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error while working with fstab:\n{e.stderr.strip()}")
    elif user_answer == "n":
        print("ℹ️ Alright. Remember: you'll need to mount it manually after each reboot.")
        print(f"   Command: sudo mount --bind {workshop_dir} {mods_dir}")
    else:
        print("⚠️ Invalid answer. Operation canceled. The current mount will remain active until reboot.")
