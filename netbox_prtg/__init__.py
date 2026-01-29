"""
NetBox PRTG Plugin

Display PRTG Network Monitor status on Device and VirtualMachine detail pages.
Shows sensor summary with counts by status (up/warning/down/paused).
"""

import logging

from django.db.models.signals import post_migrate
from netbox.plugins import PluginConfig

__version__ = "0.2.1"

logger = logging.getLogger(__name__)


def create_custom_fields(sender, **kwargs):
    """Create custom fields for PRTG data after migrations complete."""
    # Only run for this plugin's migrations
    if sender.name != "netbox_prtg":
        return

    from django.contrib.contenttypes.models import ContentType
    from django.db import OperationalError, ProgrammingError

    try:
        from dcim.models import Device
        from extras.models import CustomField
        from virtualization.models import VirtualMachine

        device_ct = ContentType.objects.get_for_model(Device)
        vm_ct = ContentType.objects.get_for_model(VirtualMachine)

        # Define custom fields
        fields_config = [
            {
                "name": "prtg_device_id",
                "label": "PRTG Device ID",
                "type": "integer",
                "description": "PRTG device object ID for direct linking (optional)",
            },
        ]

        for field_config in fields_config:
            defaults = {
                "label": field_config["label"],
                "type": field_config["type"],
                "description": field_config["description"],
                "group_name": "PRTG Monitoring",
                "ui_visible": "if-set",
                "ui_editable": "yes",
            }

            cf, created = CustomField.objects.get_or_create(
                name=field_config["name"],
                defaults=defaults,
            )

            # Ensure field is assigned to Device and VirtualMachine models
            if device_ct not in cf.object_types.all():
                cf.object_types.add(device_ct)
            if vm_ct not in cf.object_types.all():
                cf.object_types.add(vm_ct)

            if created:
                logger.info(f"Created custom field: {field_config['name']}")

    except (OperationalError, ProgrammingError):
        # Database not ready (e.g., during migrations)
        pass
    except Exception as e:
        logger.warning(f"Could not create custom fields: {e}")


class PRTGConfig(PluginConfig):
    """Plugin configuration for NetBox PRTG integration."""

    name = "netbox_prtg"
    verbose_name = "PRTG Monitoring"
    description = "Display PRTG monitoring status on device pages"
    version = __version__
    author = "sieteunoseis"
    author_email = "jeremy.worden@gmail.com"
    base_url = "prtg"
    min_version = "4.0.0"

    # Required settings - plugin won't load without these
    required_settings = []

    # Default configuration values
    default_settings = {
        "prtg_url": "",  # PRTG server URL (e.g., https://prtg.example.com)
        "prtg_api_token": "",  # API token from PRTG account settings
        "timeout": 30,  # API timeout in seconds
        "cache_timeout": 60,  # Cache sensor data for 60 seconds
        "verify_ssl": True,  # SSL verification (default True for security)
    }

    def ready(self):
        """Register signal to create custom fields after migrations."""
        super().ready()
        post_migrate.connect(create_custom_fields, sender=self)


config = PRTGConfig
