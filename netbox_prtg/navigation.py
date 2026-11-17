"""
Navigation menu for NetBox PRTG plugin.
"""

from django.conf import settings
from netbox.plugins import PluginMenu, PluginMenuItem

_menu = PluginMenu(
    label="PRTG",
    groups=(
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_prtg:settings",
                    link_text="Configuration",
                    permissions=["netbox_prtg.configure_prtg"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-monitor-dashboard",
)


# top_level_menu=False puts this plugin's items under the shared "Plugins" menu
# (grouped by plugin name) instead of its own top-level sidebar menu.
if settings.PLUGINS_CONFIG.get("netbox_prtg", {}).get("top_level_menu", True):
    menu = _menu
else:
    menu_items = tuple(item for group in _menu.groups for item in group.items)
