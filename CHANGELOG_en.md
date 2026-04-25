 # Changelog

## Ver [2.1.0] - 2026-04-25

### Added
- Added a command to display available games for unlocking (*the ability to unlock other games is currently under development*).

### Changed
- The project architecture has been completely reviewed and redesigned.
- A dedicated **S3 Bucket** has been deployed and integrated for storing DLC files. The project is now independent of third-party resources.


## Ver [2.0.0] - 2026-04-21
### Fixed
- **The `libsteam_api.so` library source has been changed. (*Previously, the library was non-functional!*). A fork of the Goldberg Emulator library is now used (https://github.com/Detanup01/gbe_fork).**
- Changes to library loading functions.

### Added
- Added configs for customizing the Steam library emulation behavior.

### Changed
- Changed parsing of available DLC data.
- Full test coverage of new functions.


## Ver [1.1.0.dev2] - 2026-04-20 [<u>DEPRECATED!</u>]
### Added
- DLC file hash checking. The utility now downloads only missing content.
- The `--force` flag allows you to download and unpack DLC even if it already exists in the DLC folder.

---

## Ver [1.0.0] - 2026-04-18 [<u>DEPRECATED!</u>]
### Changed
- General code refactoring.
- Changed the utility installation method (*now everything is done via `pipx/pip`*).
- Code is now covered by tests (*with AI assistance*).
- Changed the **DLC** download method. Now everything is done using Python without **wget** as before.
- Version numbering has begun.