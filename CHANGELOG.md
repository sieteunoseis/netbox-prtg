# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
