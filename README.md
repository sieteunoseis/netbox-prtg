# NetBox PRTG Plugin

<img src="docs/icon.png" alt="NetBox PRTG Plugin" width="100" align="right">

A NetBox plugin that displays PRTG Network Monitor status on Device and Virtual Machine detail pages.

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/sieteunoseis/netbox-prtg/actions/workflows/ci.yml/badge.svg)](https://github.com/sieteunoseis/netbox-prtg/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/netbox-prtg)](https://pypi.org/project/netbox-prtg/)

## Features

- **Device Tab**: Shows PRTG monitoring summary on device detail pages
- **Virtual Machine Tab**: Shows PRTG monitoring summary on VM detail pages
- **Sensor Summary**: Displays sensor counts by status (Up, Warning, Down, Paused)
- **Export to PRTG**: Create devices in PRTG directly from NetBox with auto-discovery
- **Virtual Chassis Support**: Monitors entire stack using VC name and master IP
- **Direct Links**: Quick link to view the device in PRTG
- **Caching**: Configurable caching to minimize API calls
- **Custom Field**: Optional `prtg_device_id` field for explicit device mapping

## Screenshots

### Device Tab
Shows sensor status summary with color-coded badges for quick status overview.

![Device Tab](https://raw.githubusercontent.com/sieteunoseis/netbox-prtg/main/screenshots/netbox-prtg-device.png)

### Export to PRTG
Export devices from NetBox to PRTG with one click.

![Export](https://raw.githubusercontent.com/sieteunoseis/netbox-prtg/main/screenshots/netbox-prtg-export.png)

### Settings Page
Displays current configuration and connection status.

![Settings Page](https://raw.githubusercontent.com/sieteunoseis/netbox-prtg/main/screenshots/netbox-prtg-settings.png)

## Requirements

- NetBox 4.0.0 or higher
- PRTG Network Monitor with API access
- PRTG API Token

> **Note:** This plugin is developed and tested exclusively on NetBox 4.x. It is not compatible with NetBox 3.x due to API and model changes.

## Installation

### Via pip (recommended)

```bash
pip install netbox-prtg
```

### From source

```bash
git clone https://github.com/sieteunoseis/netbox-prtg.git
cd netbox-prtg
pip install .
```

## Configuration

1. Add the plugin to your NetBox `configuration.py`:

```python
PLUGINS = [
    'netbox_prtg',
]

PLUGINS_CONFIG = {
    'netbox_prtg': {
        'prtg_url': 'https://prtg.example.com',
        'prtg_api_token': 'your-api-token-here',
        'timeout': 30,
        'cache_timeout': 60,
        'verify_ssl': True,
    }
}
```

2. Restart NetBox to load the plugin.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `prtg_url` | string | `""` | PRTG server URL (e.g., `https://prtg.example.com`) |
| `prtg_api_token` | string | `""` | API token from PRTG account settings |
| `timeout` | int | `30` | API request timeout in seconds |
| `cache_timeout` | int | `60` | How long to cache API responses in seconds |
| `verify_ssl` | bool | `True` | Verify SSL certificates |

### Getting a PRTG API Token

1. Log into your PRTG web interface
2. Go to **Setup** > **Account Settings** > **My Account**
3. Under **API Keys**, click **Create API Key**
4. Copy the token and add it to your NetBox configuration

## Usage

### Device Matching

The plugin matches NetBox devices to PRTG devices by hostname. The device name in NetBox must match the device name in PRTG.

For explicit mapping, you can set the `prtg_device_id` custom field on a device with the PRTG object ID.

### Virtual Chassis Support

For devices that are members of a Virtual Chassis (VC), the plugin:
- Uses the **VC name** for PRTG device lookup/export (not individual member names)
- Uses the **VC master's IP address** as the host for monitoring
- Displays VC information in the PRTG tab

This allows you to monitor an entire switch stack as a single PRTG device.

### Viewing Monitoring Status

1. Navigate to any device or virtual machine detail page
2. Click the **PRTG** tab
3. View the sensor status summary

### Exporting Devices to PRTG

When a device is not found in PRTG, you can export it directly:

1. Click the **Export to PRTG** button
2. The device is created in the "NetBox Import" group
3. Auto-discovery runs to detect available sensors
4. Move the device to the appropriate group in PRTG as needed

### Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| Up | Green | Sensor is healthy |
| Warning | Orange | Sensor has warnings |
| Down | Red | Sensor is down/critical |
| Paused | Gray | Sensor is paused |
| Unusual | Amber | Sensor has unusual readings |

## Development

### Setup

```bash
cd ~/development
git clone https://github.com/sieteunoseis/netbox-prtg.git
cd netbox-prtg
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Lint Checks

```bash
black netbox_prtg/
isort netbox_prtg/
flake8 netbox_prtg/
```

### Testing with NetBox Dev Instance

1. Add to `netbox-dev/configuration/plugins.py`
2. Mount in `netbox-dev/docker-compose.yml`
3. Restart: `docker-compose restart netbox`

## API Endpoints Used

The plugin uses the following PRTG API endpoints:

- `GET /api/status.json` - Test connection
- `GET /api/table.json?content=devices` - Find devices by hostname
- `GET /api/table.json?content=sensors` - Get device sensors
- `GET /api/table.json?content=groups` - Find groups
- `GET /api/addgroup.htm` - Create groups
- `GET /api/adddevice2.htm` - Create devices with auto-discovery

## Future Enhancements

- [ ] Detailed sensor list view
- [ ] Sensor alerts history
- [ ] Bulk device status view
- [ ] Conditional tab visibility

## License

Apache License 2.0

## Author

- **sieteunoseis** - [GitHub](https://github.com/sieteunoseis)

## Links

- [GitHub Repository](https://github.com/sieteunoseis/netbox-prtg)
- [PyPI Package](https://pypi.org/project/netbox-prtg/)
- [Issue Tracker](https://github.com/sieteunoseis/netbox-prtg/issues)
- [Wiki](https://github.com/sieteunoseis/netbox-prtg/wiki)
- [Changelog](https://github.com/sieteunoseis/netbox-prtg/blob/main/CHANGELOG.md)
- [PRTG API Documentation](https://www.paessler.com/manuals/prtg/http_api)
