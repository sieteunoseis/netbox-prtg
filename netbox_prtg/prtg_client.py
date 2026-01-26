"""
PRTG Network Monitor API Client

Provides methods to interact with PRTG API for device and sensor information.
Includes caching to minimize API calls.
"""

import logging
from typing import Optional
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PRTGClient:
    """Client for PRTG Network Monitor API."""

    def __init__(
        self,
        url: str,
        api_token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        cache_timeout: int = 60,
    ):
        """
        Initialize PRTG API client.

        Args:
            url: PRTG server URL (e.g., https://prtg.example.com)
            api_token: API token from PRTG account settings
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            cache_timeout: How long to cache responses in seconds
        """
        self.base_url = url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.cache_timeout = cache_timeout

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make authenticated request to PRTG API.

        Args:
            endpoint: API endpoint path
            params: Query parameters (apitoken added automatically)

        Returns:
            dict: Response data or {"error": "message"}
        """
        url = urljoin(self.base_url, endpoint)

        if params is None:
            params = {}
        params["apitoken"] = self.api_token

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            logger.error(f"PRTG API request timed out: {endpoint}")
            return {"error": "Request timed out"}
        except requests.ConnectionError as e:
            logger.error(f"PRTG API connection error: {e}")
            return {"error": f"Connection failed: {e}"}
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("PRTG API authentication failed - check API token")
                return {"error": "Authentication failed - check API token"}
            logger.error(f"PRTG API HTTP error: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.RequestException as e:
            logger.error(f"PRTG API request failed: {e}")
            return {"error": str(e)}
        except ValueError as e:
            logger.error(f"PRTG API invalid JSON response: {e}")
            return {"error": "Invalid response from PRTG"}

    def test_connection(self) -> dict:
        """
        Test connection to PRTG server.

        Returns:
            dict: {"success": True, "version": "..."} or {"error": "message"}
        """
        result = self._make_request("/api/status.json")

        if "error" in result:
            return result

        # Extract version info from status response
        version = result.get("Version", result.get("version", "Unknown"))
        return {
            "success": True,
            "version": version,
            "message": f"Connected to PRTG {version}",
        }

    def find_device_by_hostname(self, hostname: str) -> Optional[dict]:
        """
        Find a device in PRTG by hostname.

        Args:
            hostname: Device hostname to search for

        Returns:
            dict: Device info with objid, name, host, status or None if not found
        """
        cache_key = f"prtg_device_{hostname.lower()}"
        cached = cache.get(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

        # Search for device by name (substring match)
        params = {
            "content": "devices",
            "columns": "objid,name,host,status,message,group",
            "filter_name": f"@sub({hostname})",
            "count": "50",
        }

        result = self._make_request("/api/table.json", params)

        if "error" in result:
            logger.warning(f"PRTG device search failed: {result['error']}")
            return None

        devices = result.get("devices", [])

        if not devices:
            # Try exact match on host field
            params["filter_name"] = ""
            params["filter_host"] = f"@sub({hostname})"
            result = self._make_request("/api/table.json", params)

            if "error" not in result:
                devices = result.get("devices", [])

        if not devices:
            logger.debug(f"Device '{hostname}' not found in PRTG")
            return None

        # Find best match - prefer exact name match
        device = None
        hostname_lower = hostname.lower()

        for d in devices:
            device_name = d.get("name", "").lower()
            device_host = d.get("host", "").lower()

            # Exact name match
            if device_name == hostname_lower:
                device = d
                break
            # Exact host match
            elif device_host == hostname_lower:
                device = d
                break
            # Partial match - take first one
            elif device is None:
                device = d

        if device:
            device["cached"] = False
            cache.set(cache_key, device, self.cache_timeout)
            return device

        return None

    def get_device_sensors(self, device_id: int) -> list:
        """
        Get all sensors for a device.

        Args:
            device_id: PRTG device object ID

        Returns:
            list: List of sensor dicts with objid, name, status, lastvalue, message
        """
        cache_key = f"prtg_sensors_{device_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        params = {
            "content": "sensors",
            "columns": "objid,name,status,lastvalue,message,priority,type",
            "filter_parentid": str(device_id),
            "count": "*",
        }

        result = self._make_request("/api/table.json", params)

        if "error" in result:
            logger.warning(f"Failed to get sensors for device {device_id}: {result['error']}")
            return []

        sensors = result.get("sensors", [])
        cache.set(cache_key, sensors, self.cache_timeout)
        return sensors

    def get_device_summary(self, device_id: int) -> dict:
        """
        Get sensor summary counts for a device.

        Args:
            device_id: PRTG device object ID

        Returns:
            dict: {up: N, warning: N, down: N, paused: N, unusual: N, total: N}
        """
        sensors = self.get_device_sensors(device_id)

        summary = {
            "up": 0,
            "warning": 0,
            "down": 0,
            "paused": 0,
            "unusual": 0,
            "unknown": 0,
            "total": len(sensors),
        }

        for sensor in sensors:
            status = sensor.get("status", "").lower()
            status_raw = sensor.get("status_raw", 0)

            # Map PRTG status to categories
            # Status values: Up, Warning, Down, Paused, Unknown, Unusual
            if "up" in status or status_raw == 3:
                summary["up"] += 1
            elif "warning" in status or status_raw == 4:
                summary["warning"] += 1
            elif "down" in status or status_raw == 5:
                summary["down"] += 1
            elif "paused" in status or status_raw in (7, 8, 9, 11, 12):
                summary["paused"] += 1
            elif "unusual" in status or status_raw == 10:
                summary["unusual"] += 1
            else:
                summary["unknown"] += 1

        return summary

    def get_device_url(self, device_id: int) -> str:
        """
        Get the URL to view a device in PRTG web interface.

        Args:
            device_id: PRTG device object ID

        Returns:
            str: Full URL to device page
        """
        return f"{self.base_url}/device.htm?id={device_id}"

    def find_group_by_name(self, group_name: str) -> Optional[dict]:
        """
        Find a group in PRTG by name.

        Args:
            group_name: Group name to search for

        Returns:
            dict: Group info with objid, name or None if not found
        """
        params = {
            "content": "groups",
            "columns": "objid,name,group",
            "filter_name": group_name,
            "count": "50",
        }

        result = self._make_request("/api/table.json", params)

        if "error" in result:
            logger.warning(f"PRTG group search failed: {result['error']}")
            return None

        groups = result.get("groups", [])

        # Find exact match
        for g in groups:
            if g.get("name", "").lower() == group_name.lower():
                return g

        return None

    def get_or_create_import_group(self, parent_group_id: int = 0) -> Optional[dict]:
        """
        Get or create the 'NetBox Import' group for device imports.

        Args:
            parent_group_id: Parent group ID (0 = root/probe)

        Returns:
            dict: Group info with objid, name or None on failure
        """
        group_name = "NetBox Import"

        # Check if group already exists
        existing = self.find_group_by_name(group_name)
        if existing:
            return existing

        # Create the group using addgroup2.htm
        # Note: This requires appropriate permissions
        params = {
            "name_": group_name,
            "id": str(parent_group_id) if parent_group_id else "1",  # 1 = Local Probe typically
        }

        url = f"{self.base_url}/api/addgroup.htm"
        params["apitoken"] = self.api_token

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            # PRTG returns the new object ID in the response
            # Try to find the newly created group
            new_group = self.find_group_by_name(group_name)
            if new_group:
                logger.info(f"Created PRTG group: {group_name}")
                return new_group

            return {"error": "Group created but could not be found"}

        except requests.RequestException as e:
            logger.error(f"Failed to create PRTG group: {e}")
            return None

    def create_device(
        self,
        name: str,
        host: str,
        group_id: int,
        auto_discover: bool = True,
    ) -> dict:
        """
        Create a new device in PRTG.

        Args:
            name: Device name
            host: IP address or hostname
            group_id: Parent group ID
            auto_discover: Enable auto-discovery for sensors

        Returns:
            dict: {"success": True, "device_id": N, "message": "..."} or {"error": "..."}
        """
        # Use adddevice2.htm endpoint
        params = {
            "name_": name,
            "host_": host,
            "id": str(group_id),
            "devicetemplate_": "1",  # Auto-discovery template
            "discoverytype_": "1" if auto_discover else "0",  # 1 = auto-discovery
            "discoveryschedule_": "0",  # Run immediately
        }

        url = f"{self.base_url}/api/adddevice2.htm"
        params["apitoken"] = self.api_token

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            # Check response for success
            # PRTG typically returns HTML with the new device ID
            response_text = response.text

            # Try to find the device we just created
            new_device = self.find_device_by_hostname(name)
            if new_device:
                # Clear the cache so we get fresh data
                cache_key = f"prtg_device_{name.lower()}"
                cache.delete(cache_key)

                return {
                    "success": True,
                    "device_id": new_device.get("objid"),
                    "message": f"Device '{name}' created in PRTG",
                    "device_url": self.get_device_url(new_device.get("objid")),
                }

            # Device might take a moment to appear, check response
            if "objid" in response_text.lower() or response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Device '{name}' created in PRTG (may take a moment to appear)",
                }

            return {"error": "Device creation response unclear - check PRTG manually"}

        except requests.HTTPError as e:
            if e.response.status_code == 400:
                return {"error": "Bad request - device may already exist or invalid parameters"}
            logger.error(f"Failed to create PRTG device: {e}")
            return {"error": f"HTTP error: {e}"}
        except requests.RequestException as e:
            logger.error(f"Failed to create PRTG device: {e}")
            return {"error": str(e)}

    def export_device_from_netbox(self, name: str, host: str) -> dict:
        """
        Export a device from NetBox to PRTG.

        Creates the device in the 'NetBox Import' group with auto-discovery enabled.

        Args:
            name: Device name from NetBox
            host: IP address or hostname

        Returns:
            dict: {"success": True, ...} or {"error": "..."}
        """
        # First check if device already exists
        existing = self.find_device_by_hostname(name)
        if existing:
            return {
                "error": f"Device '{name}' already exists in PRTG",
                "device_id": existing.get("objid"),
                "device_url": self.get_device_url(existing.get("objid")),
            }

        # Get or create the import group
        import_group = self.get_or_create_import_group()
        if not import_group or "error" in import_group:
            # Fall back to creating in root probe (id=1)
            logger.warning("Could not find/create NetBox Import group, using root probe")
            group_id = 1
        else:
            group_id = import_group.get("objid", 1)

        # Create the device
        result = self.create_device(
            name=name,
            host=host,
            group_id=group_id,
            auto_discover=True,
        )

        return result


def get_client() -> Optional[PRTGClient]:
    """
    Factory function to get configured PRTG client.

    Returns:
        PRTGClient instance or None if not configured
    """
    config = settings.PLUGINS_CONFIG.get("netbox_prtg", {})

    prtg_url = config.get("prtg_url")
    api_token = config.get("prtg_api_token")

    if not prtg_url or not api_token:
        logger.warning("PRTG plugin not configured - missing prtg_url or prtg_api_token")
        return None

    return PRTGClient(
        url=prtg_url,
        api_token=api_token,
        timeout=config.get("timeout", 30),
        verify_ssl=config.get("verify_ssl", True),
        cache_timeout=config.get("cache_timeout", 60),
    )
