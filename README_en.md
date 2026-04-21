# Linux DLC Unlocker Tool (ldu-tool)

[![PyPI](https://img.shields.io/pypi/v/ldu-tool.svg)](https://pypi.org/project/ldu-tool)


A Python utility for automatically unlocking all **Stellaris** game DLCs in a Linux environment (Steam). The script uses the Steam API emulator (Goldberg Emulator) and automatically downloads the necessary content files.

> ⚠️ This utility is **NOT** intended for unlocking DLC on **Windows**! Similar software for Windows can be found in **[this repository](https://github.com/seuyh/stellaris-dlc-unlocker)**.
> 
> To download DLCs, this utility uses a remote file server from the **[same repository](https://github.com/seuyh/stellaris-dlc-unlocker)**. Thanks to [seuyh](https://github.com/seuyh) for providing this convenience.

## 📋 Requirements

- **Python 3.8+**
- **Libraries: `requests`, `tqdm>=4.67.3`, `dirhash==0.5.0`**
- Internet access (VPN may be required to access `api.steamcmd.net` from some regions, including Russia)
- Write permissions for the game installation directory

## 🚀 Installation and Launch

Installation is performed via **`pipx`** (*recommended*) or **`pip`**.

1. If you don't have `pipx` installed, install it (*example for **Arch Linux***):
```bash
pacman -S python-pipx
```
2. Next, install the `ldu-tool` itself:
```bash
pipx install ldu-tool
```
3. Verify that `ldu-tool` was installed correctly:
```bash
ldu-tool --version
```
If the utility version is displayed, it means you did everything correctly!

**Alternative installation option (*working with source code*):**
1. Clone this repository to a convenient location:
```bash
git clone https://github.com/IAMVanilka/linux-dlc-unlocker-tool 
```
2. Navigate to the repository folder:
```bash
cd linux-dlc-unlocker-tool
```
3. Create a virtual environment (*requires **python-env***):
```bash
python -m venv .venv
```
4. Activate the environment:
```bash
source venv/bin/activate
OR
source venv/bin/activate.fish # If you use fish instead of bash
```
5. Install dependencies:
```bash
pip install -r requirements.txt
```
6. Verify the utility is working:
```bash
python -m modules.main --version
```
If the utility version is displayed, it means you did everything correctly!

## ⚙️ Command List

| Command | Description |
|---------|-------------|
| **Common** |
| `ldu-tool -V/--version`| Show tool verison|
| `ldu-tool -h/--help` / `ldu-tool install -h/--help` | Display command help |
| **Install** |
| `ldu-tool install` | Starts basic installation in the directory where the script is located. Downloads DLC and the modified `libsteam_api.so` library |
| `ldu-tool install --path/-p <PATH_TO_GAME>` | Starts basic installation at the specified path. Downloads DLC and the modified `libsteam_api.so` library |
| `ldu-tool install --dlc` | Downloads **only DLCs** from the remote server |
| `ldu-tool install --libs/-l` | Downloads **only `libsteam_api.so`** from the remote server |
|`ldu-tool install --force/-f`|Downloads and unpacks DLCs even if they are already installed|

## 🔍 How It Works?

1. **Directory Check:** The script searches for the `stellaris` binary in the specified folder. If it is not found, it prompts the user for confirmation.
2. **API Emulator:** Downloads the latest build of `libsteam_api.so` from the **[fork of the Goldberg Emulator GitLab repository](https://github.com/Detanup01/gbe_fork)** and places it in the game's root directory.
3. **DLC Setup:** Creates the `steam_settings/` folder and the `configs.app.ini` file, populating it with the `dlc_id:name` of all official DLCs via the public API `api.steamcmd.net`.
4. **Download Content:** Downloads ZIP archives with DLC files from the external file server specified in `data.json` in **[this repository](https://github.com/seuyh/stellaris-dlc-unlocker)**.
5. **Unpack:** Extracts the archive contents to the `dlc/` folder and automatically deletes the original `.zip` files.
6. **Run (optional):** After installation, offers to launch the game through Steam using the `steam://run/281990` protocol.

## 📂 File Structure After Installation

```
/path/to/Stellaris/
├── stellaris              # Main game executable
├── libsteam_api.so        # Steam API Emulator (Goldberg)
├── steam_settings/
│   └── steam_appid.txt
        configs.app.ini    # Emulator settings and DLCs information.
└── dlc/                   # Unpacked DLCs content
```

## ❓ Troubleshooting

- **Connection error to `api.steamcmd.net`:** Try using a VPN or proxy if you are in a region with access restrictions.

- **`PermissionError` when creating folders:** Make sure your user has write permissions to the game folder. Do not run the script with `sudo`; instead, change the folder owner via `chown -R $USER:$USER /path/to/Stellaris` (recursively changes the owner of the folder and all its contents to the current user).

- **Game doesn't see DLCs:** Check that `libsteam_api.so` is in the same directory as the `stellaris` binary, and that the `dlc/` folder contains unpacked files, not archives. Check the `steam_settings/configs.app.ini` file. Inside, there should be a `[app::dlcs]` section with all DLCs in the format `dlc_id = dlc_name`. If everything seems fine and nothing works, open an [issue](https://github.com/IAMVanilka/linux-dlc-unlocker-tool/issues/new) and we'll discuss it.

- **Lost saves:** When using a modified `libsteam_api.so` library, you will have to give up **Steam Cloud Saves**, as the library intercepts all requests to the **Steam API**. **Game saves are written to:** `~/.local/share/Paradox Interactive/Stellaris/save games/`. If you need to transfer saves to another device, you'll have to do it manually (**like a true pirate!**).

## 📜 License

This project is distributed **"as is"**. The author is not responsible for any possible consequences of using this utility. Use at your own risk.
