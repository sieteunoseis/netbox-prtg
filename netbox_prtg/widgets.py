"""Dashboard widgets for the NetBox PRTG plugin."""

import logging

from django import forms
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from extras.dashboard.utils import register_widget
from extras.dashboard.widgets import DashboardWidget, WidgetConfigForm

from .prtg_client import get_client

logger = logging.getLogger(__name__)


@register_widget
class PRTGStatusWidget(DashboardWidget):
    """Dashboard widget showing aggregate PRTG sensor status counts."""

    default_title = _("PRTG Status")
    description = _("Display aggregate sensor status counts from PRTG Network Monitor.")
    template_name = "netbox_prtg/widgets/prtg_status.html"
    width = 4
    height = 3

    class ConfigForm(WidgetConfigForm):
        cache_timeout = forms.IntegerField(
            min_value=60,
            max_value=3600,
            initial=300,
            required=False,
            label=_("Cache timeout (seconds)"),
            help_text=_("How long to cache PRTG sensor data (60-3600 seconds)."),
        )

    def render(self, request):
        client = get_client()
        if not client:
            return render_to_string(
                self.template_name,
                {
                    "error": "PRTG not configured. Set prtg_url and prtg_api_token in plugin settings.",
                },
            )

        cache_timeout = self.config.get("cache_timeout", 300)
        summary = client.get_aggregate_sensor_summary(cache_timeout=cache_timeout)

        if "error" in summary:
            return render_to_string(
                self.template_name,
                {
                    "error": summary["error"],
                },
            )

        # Build status list with display properties
        status_defs = [
            ("up", "Up", "bg-success", "text-white"),
            ("warning", "Warning", "bg-warning", "text-dark"),
            ("down", "Down", "bg-danger", "text-white"),
            ("paused", "Paused", "bg-secondary", "text-white"),
            ("unusual", "Unusual", None, "text-white"),  # custom color
            ("unknown", "Unknown", "bg-dark", "text-white"),
        ]

        statuses = []
        for key, label, bg_class, text_class in status_defs:
            count = summary.get(key, 0)
            # Skip unusual/unknown if zero
            if key in ("unusual", "unknown") and count == 0:
                continue
            statuses.append(
                {
                    "key": key,
                    "label": label,
                    "count": count,
                    "bg_class": bg_class,
                    "text_class": text_class,
                }
            )

        prtg_url = client.base_url

        return render_to_string(
            self.template_name,
            {
                "statuses": statuses,
                "total": summary.get("total", 0),
                "prtg_url": prtg_url,
                "cached": summary.get("cached", False),
            },
        )
