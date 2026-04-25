#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IAMVanilka

from ._version import __version__
from .games.base_strategy import BaseGameStrategy
from .utils import files_hash_check, unzip_files, run_the_game
from .games.stellaris.stellaris_strategy import StellarisStrategy

from enum import Enum

import typer

class GameChoice(str, Enum):
    stellaris = "stellaris"

GAME_METADATA = {
    GameChoice.stellaris: {"patch_name":["GDE Fork (by Detanup01)"], "full_name": "Stellaris"},
}

class DLCTool:
    def __init__(self, strategy: BaseGameStrategy):
        self.strategy = strategy

    def default_install_scenario(self, force=False):
        if force:
            dlcs_to_download = self.strategy.dlc_files_validation_hashes
        else:
            dlcs_to_download = files_hash_check(self.strategy.dlc_dir, self.strategy.dlc_files_validation_hashes)
        dlcs_list = self.strategy.get_dlcs_list()

        self.strategy.download_library()
        self.strategy.create_configs(dlcs_list)
        self.strategy.download_dlcs(dlcs_to_download)    
        unzip_files(self.strategy.dlc_dir)

        if typer.confirm("Installing done! Launch the game? (only for Steam)"):
            run_the_game(self.strategy.app_id)

    def install_only_dlcs(self, force=False):
        if force:
            dlcs_to_download = self.strategy.dlc_files_validation_hashes
        else:
            dlcs_to_download = files_hash_check(self.strategy.dlc_dir, self.strategy.dlc_files_validation_hashes)
        self.strategy.download_dlcs(data_to_download=dlcs_to_download)
        unzip_files(self.strategy.dlc_dir)

    def install_only_libs(self):
        dlcs_list = self.strategy.get_dlcs_list()

        self.strategy.download_library()
        self.strategy.create_configs(dlcs_list)
    

app = typer.Typer(help="Linux DLC Unlocker Tool - unlocks all DLCs for Stellaris game.")

@app.callback(invoke_without_command=True)
def global_options(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Print current app version and exit.")
    ):
    if version:
        typer.secho(f"Linux DLC Unlocker Tool version {__version__}", fg=typer.colors.GREEN, bold=True)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command()
def install(
    game: GameChoice | None = typer.Argument(None, help="Название игры (stellaris, ck3, hoi4)"),
    dlc: bool = typer.Option(False, "--dlc", help="Install DLCs"),
    libs: bool = typer.Option(False, "-l", "--libs", help="Install libs"),
    path: str | None = typer.Option(None, "-p", "--path", help="Install by specifying the path to the game."),
    force: bool = typer.Option(False, "-f", "--force", help="Reinstall all DLCs even if they have already been downloaded.")
    ):
    """Install libs and DLCs"""

    if game is None:
        if typer.confirm("Install unlocker for Stellaris?"):
            game = GameChoice.stellaris
        else:
            typer.secho("\nRestart tool with game in arguments:", bold=True)
            typer.secho("💡 Example: ldu-tool install ck3 -p /path/to/game.", fg=typer.colors.BRIGHT_YELLOW)
            typer.secho("💡 You also can see available games using: ldu-tool list.\n", fg=typer.colors.BRIGHT_YELLOW)
            raise typer.Exit(code=1)

    class_map = {
        GameChoice.stellaris: StellarisStrategy,
    }

    strategy = class_map[game]
    tool = DLCTool(strategy(path))

    tool.strategy.check_game_dir()

    if dlc:
        print(f"Only DLCs mode. {'[FORCED]' if force else ''}")
        tool.install_only_dlcs(force=force)
    if libs:
        print("Mock libs install")
    if not dlc and not libs:
        print(f"Default install scenario for {game.name} started. {'[FORCED]' if force else ''}")
        tool.default_install_scenario(force=force)

@app.command()
def list():
    """Get list of available games"""

    i = 0
    typer.secho(f"\nAvailable games:", bold=True)

    for game in GameChoice:
        i += 1
        typer.secho(f"  {i}.{GAME_METADATA[game]["full_name"]} {GAME_METADATA[game]["patch_name"]}", fg=typer.colors.BLUE)

    typer.secho("\nSupport for additional games is planned for future releases.", fg=typer.colors.BRIGHT_YELLOW, bold=True)

    print()

if __name__ == "__main__":
    app()