# Linux DLC Unlocker Tool (ldu-tool)

[![PyPI](https://img.shields.io/pypi/v/ldu-tool.svg)](https://pypi.org/project/ldu-tool)


A Python utility for automatically unlocking all **Stellaris** game DLCs in a Linux environment (Steam). The script uses the Steam API emulator (Goldberg Emulator) and automatically downloads the necessary content files.

> ⚠️ This utility is **NOT** intended for unlocking DLC on **Windows**! Similar software for Windows can be found in **[this repository](https://github.com/seuyh/stellaris-dlc-unlocker)**.
> 
> To download DLCs, this utility uses a remote file server from the **[same repository](https://github.com/seuyh/stellaris-dlc-unlocker)**. Thanks to [seuyh](https://github.com/seuyh) for providing this convenience.

## 📋 Requirements

- **Python 3.6+**
- **`requests`** library
- **`wget`** (standard Linux utility for downloading files via HTTP/HTTPS)
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
python modules/main.py --version
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
| `ldu-tool install --dlc` | Downloads **only DLC** from the remote server |
| `ldu-tool install --libs/-l` | Downloads **only `libsteam_api.so`** from the remote server |

## 🔍 How It Works?

1. **Directory Check:** The script looks for the `stellaris` binary file in the specified folder. If not found, it prompts the user for confirmation.
2. **API Emulator:** Downloads the latest build of `libsteam_api.so` from the Goldberg Emulator GitLab repository and places it in the game root.
3. **DLC Setup:** Creates the `steam_settings/` folder and the `dlc.txt` file, populating it with IDs of all official DLCs via the public API `api.steamcmd.net`.
4. **Content Download:** Downloads ZIP archives with DLC files from an external file server specified in `data.json` in **[this repository](https://github.com/seuyh/stellaris-dlc-unlocker)**.
5. **Extraction:** Extracts the archive contents into the `dlc/` folder and automatically deletes the original `.zip` files.
6. **Launch (optional):** After installation, offers to launch the game via Steam using the `steam://run/281990` protocol.

## 📂 File Structure After Installation

```
/path/to/Stellaris/
├── stellaris              # Main game executable
├── libsteam_api.so        # Steam API Emulator (Goldberg)
├── steam_settings/
│   └── dlc.txt            # List of IDs for all unlocked DLCs
└── dlc/                   # Unpacked DLC content files
```

## ❓ Troubleshooting

- **Connection error to `api.steamcmd.net`:** Try using a VPN or proxy if you are in a region with restricted access.
- **`PermissionError` when creating folders:** Ensure your user has write permissions for the game folder. Do not run the script with `sudo`; instead, change the folder owner via `chown -R $USER:$USER /path/to/Stellaris` (recursively changes the owner of the folder and all its subfiles to the current user).
- **Game does not see DLC:** Check that `libsteam_api.so` is in the same directory as the `stellaris` binary, and that the `dlc/` folder contains unpacked files, not archives.

## 📜 License

This project is distributed **"as is"**. The author is not responsible for any possible consequences of using this utility. Use at your own risk.
