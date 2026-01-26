"""
URL routing for NetBox PRTG plugin.
"""

from django.urls import path

from .views import ExportDeviceView, PRTGSettingsView, TestConnectionView

urlpatterns = [
    path("settings/", PRTGSettingsView.as_view(), name="settings"),
    path("test-connection/", TestConnectionView.as_view(), name="test_connection"),
    path("export-device/<int:pk>/", ExportDeviceView.as_view(), name="export_device"),
    path("export-vm/<int:pk>/", ExportDeviceView.as_view(), name="export_vm"),
]
