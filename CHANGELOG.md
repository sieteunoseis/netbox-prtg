# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-11-17

### Added
- `tab_weight` setting (default `9006`) to control where this plugin's tab sits on object pages, so tab order can be set in config instead of code
- `top_level_menu` setting (default `True`); set `False` to list this plugin's menu items under the shared "Plugins" menu instead of its own top-level sidebar menu

### Changed
- Plugin display name shortened to "PRTG" (was "NetBox PRTG") so it matches the sidebar menu label

## [0.4.3] - 2026-05-05

### Fixed

- Fix `ProgrammingError: relation "netbox_prtg_prtg" does not exist` on NetBox 4.5+ when navigating to `/core/system/`. The unmanaged permission-anchor model is now flagged with `_netbox_private = True`, and a data migration sets `ObjectType.public = False` so NetBox's object-count loop excludes it.

## [0.1.0] - 2026-01-26

### Added
- Initial release
- PRTG monitoring tab on Device and VirtualMachine detail pages
- Sensor status summary showing counts by status (up/warning/down/paused)
- Export devices from NetBox to PRTG with auto-discovery
- Automatic "NetBox Import" group creation in PRTG for exported devices
- Virtual chassis support (uses VC name and master IP for monitoring)
- Caching for PRTG API responses with configurable timeout
- Settings page with connection test functionality
- Support for custom `prtg_device_id` field for direct device mapping
- Link to view device directly in PRTG web interface
