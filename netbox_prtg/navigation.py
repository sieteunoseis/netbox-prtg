"""
Navigation menu for NetBox PRTG plugin.
"""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="PRTG",
    groups=(
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_prtg:settings",
                    link_text="Configuration",
                    permissions=["dcim.view_device"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-monitor-dashboard",
)
