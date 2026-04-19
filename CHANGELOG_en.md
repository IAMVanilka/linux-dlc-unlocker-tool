 # Changelog

## [1.1.0.dev2] - 2026-04-20
### Added
- DLC file hash checking. The utility now downloads only missing content.
- The `--force` flag allows you to download and unpack DLC even if it already exists in the DLC folder.


## [1.0.0] - 2026-04-18
### Changed
- General code refactoring.
- Changed the utility installation method (*now everything is done via `pipx/pip`*).
- Code is now covered by tests (*with AI assistance*).
- Changed the **DLC** download method. Now everything is done using Python without **wget** as before.
- Version numbering has begun.