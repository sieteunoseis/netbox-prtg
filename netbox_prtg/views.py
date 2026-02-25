"""
Views for NetBox PRTG plugin.

Provides device/VM tab views and settings page.
"""

import logging

from dcim.models import Device
from django.conf import settings
from django.shortcuts import render
from netbox.views import generic
from utilities.views import ViewTab, register_model_view
from virtualization.models import VirtualMachine

from .forms import PRTGSettingsForm
from .prtg_client import get_client

logger = logging.getLogger(__name__)


def get_vc_info(device):
    """
    Get virtual chassis info for a device.

    Returns:
        tuple: (vc_name, vc_master, is_vc_member) or (None, None, False)
    """
    if not device.virtual_chassis:
        return None, None, False

    vc = device.virtual_chassis
    vc_name = vc.name
    vc_master = vc.master

    return vc_name, vc_master, True


def get_prtg_lookup_name(device):
    """
    Get the name to use for PRTG lookup.

    For VC members, returns the VC name. Otherwise returns device name.
    """
    vc_name, _, is_vc_member = get_vc_info(device)
    if is_vc_member and vc_name:
        return vc_name
    return device.name


def get_export_info(device):
    """
    Get device name and host for PRTG export.

    For VC members, returns VC name and master's IP.

    Returns:
        tuple: (name, host, is_vc, vc_master)
    """
    vc_name, vc_master, is_vc_member = get_vc_info(device)

    if is_vc_member and vc_name:
        # Use VC name
        name = vc_name

        # Use master's IP if available
        if vc_master:
            if vc_master.primary_ip4:
                host = str(vc_master.primary_ip4.address.ip)
            elif vc_master.primary_ip6:
                host = str(vc_master.primary_ip6.address.ip)
            else:
                host = vc_name
        else:
            # No master set, use VC name as host
            host = vc_name

        return name, host, True, vc_master
    else:
        # Regular device
        if device.primary_ip4:
            host = str(device.primary_ip4.address.ip)
        elif device.primary_ip6:
            host = str(device.primary_ip6.address.ip)
        else:
            host = device.name

        return device.name, host, False, None


@register_model_view(Device, name="prtg_monitoring", path="prtg")
class DevicePRTGView(generic.ObjectView):
    """Display PRTG monitoring status for a device."""

    queryset = Device.objects.all()
    template_name = "netbox_prtg/device_tab.html"
    tab = ViewTab(
        label="PRTG",
        weight=9006,
        permission="dcim.view_device",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        device = Device.objects.select_related(
            "virtual_chassis", "virtual_chassis__master", "primary_ip4", "primary_ip6"
        ).get(pk=pk)
        context = {
            "object": device,
            "tab": self.tab,
        }

        # Get PRTG client
        client = get_client()
        if not client:
            context["error"] = "PRTG not configured. Configure the plugin in NetBox settings."
            return render(request, self.template_name, context)

        # Get VC info for context
        vc_name, vc_master, is_vc_member = get_vc_info(device)
        if is_vc_member:
            context["is_vc_member"] = True
            context["vc_name"] = vc_name
            context["vc_master"] = vc_master

        # Determine lookup name (VC name for members, device name otherwise)
        lookup_name = get_prtg_lookup_name(device)

        # Check if device has a custom prtg_device_id
        prtg_device_id = None
        if hasattr(device, "custom_field_data") and device.custom_field_data:
            prtg_device_id = device.custom_field_data.get("prtg_device_id")

        prtg_device = None

        # If we have a direct device ID, use it
        if prtg_device_id:
            # Build a minimal device dict
            prtg_device = {
                "objid": prtg_device_id,
                "name": lookup_name,
                "cached": False,
            }
        else:
            # Search by hostname (VC name for members)
            prtg_device = client.find_device_by_hostname(lookup_name)

        if not prtg_device:
            context["not_found"] = True
            context["search_term"] = lookup_name
            # Add export info for the export button
            export_name, export_host, _, _ = get_export_info(device)
            context["export_name"] = export_name
            context["export_host"] = export_host
            return render(request, self.template_name, context)

        # Get sensor summary
        device_id = prtg_device.get("objid")
        summary = client.get_device_summary(device_id)

        context.update(
            {
                "prtg_device": prtg_device,
                "summary": summary,
                "prtg_url": client.base_url,
                "prtg_device_url": client.get_device_url(device_id),
                "cached": prtg_device.get("cached", False),
            }
        )

        return render(request, self.template_name, context)


@register_model_view(VirtualMachine, name="prtg_monitoring", path="prtg")
class VMPRTGView(generic.ObjectView):
    """Display PRTG monitoring status for a virtual machine."""

    queryset = VirtualMachine.objects.all()
    template_name = "netbox_prtg/device_tab.html"
    tab = ViewTab(
        label="PRTG",
        weight=9006,
        permission="virtualization.view_virtualmachine",
        hide_if_empty=False,
    )

    def get(self, request, pk):
        vm = VirtualMachine.objects.get(pk=pk)
        context = {
            "object": vm,
            "tab": self.tab,
            "is_vm": True,
        }

        # Get PRTG client
        client = get_client()
        if not client:
            context["error"] = "PRTG not configured. Configure the plugin in NetBox settings."
            return render(request, self.template_name, context)

        # Check if VM has a custom prtg_device_id
        prtg_device_id = None
        if hasattr(vm, "custom_field_data") and vm.custom_field_data:
            prtg_device_id = vm.custom_field_data.get("prtg_device_id")

        prtg_device = None

        # If we have a direct device ID, use it
        if prtg_device_id:
            prtg_device = {
                "objid": prtg_device_id,
                "name": vm.name,
                "cached": False,
            }
        else:
            # Search by hostname
            prtg_device = client.find_device_by_hostname(vm.name)

        if not prtg_device:
            context["not_found"] = True
            context["search_term"] = vm.name
            return render(request, self.template_name, context)

        # Get sensor summary
        device_id = prtg_device.get("objid")
        summary = client.get_device_summary(device_id)

        context.update(
            {
                "prtg_device": prtg_device,
                "summary": summary,
                "prtg_url": client.base_url,
                "prtg_device_url": client.get_device_url(device_id),
                "cached": prtg_device.get("cached", False),
            }
        )

        return render(request, self.template_name, context)


class PRTGSettingsView(generic.ObjectView):
    """Display PRTG plugin settings."""

    queryset = Device.objects.none()
    template_name = "netbox_prtg/settings.html"

    def get(self, request):
        config = settings.PLUGINS_CONFIG.get("netbox_prtg", {})
        form = PRTGSettingsForm(initial=config)

        # Test connection if configured
        connection_status = None
        client = get_client()
        if client:
            result = client.test_connection()
            if result.get("success"):
                connection_status = {
                    "success": True,
                    "message": result.get("message", "Connected"),
                    "version": result.get("version"),
                }
            else:
                connection_status = {
                    "success": False,
                    "message": result.get("error", "Connection failed"),
                }

        context = {
            "form": form,
            "config": config,
            "connection_status": connection_status,
            "configured": bool(config.get("prtg_url") and config.get("prtg_api_token")),
        }

        return render(request, self.template_name, context)


class TestConnectionView(generic.ObjectView):
    """Test PRTG connection endpoint."""

    queryset = Device.objects.none()

    def get(self, request):
        from django.http import JsonResponse

        client = get_client()
        if not client:
            return JsonResponse(
                {
                    "success": False,
                    "error": "PRTG not configured",
                }
            )

        result = client.test_connection()
        return JsonResponse(result)


class ExportDeviceView(generic.ObjectView):
    """Export a device to PRTG."""

    queryset = Device.objects.none()

    def post(self, request, pk):
        from django.http import JsonResponse

        # Determine if this is a Device or VM based on request path
        is_vm = "virtual-machines" in request.path

        if is_vm:
            obj = VirtualMachine.objects.select_related("primary_ip4", "primary_ip6").get(pk=pk)
            obj_type = "VM"
            # VMs don't have virtual chassis
            name = obj.name
            if obj.primary_ip4:
                host = str(obj.primary_ip4.address.ip)
            elif obj.primary_ip6:
                host = str(obj.primary_ip6.address.ip)
            else:
                host = obj.name
        else:
            obj = Device.objects.select_related(
                "virtual_chassis",
                "virtual_chassis__master",
                "virtual_chassis__master__primary_ip4",
                "virtual_chassis__master__primary_ip6",
                "primary_ip4",
                "primary_ip6",
            ).get(pk=pk)
            obj_type = "Device"
            # Use get_export_info for proper VC handling
            name, host, is_vc, vc_master = get_export_info(obj)
            if is_vc:
                obj_type = "Virtual Chassis"

        client = get_client()
        if not client:
            return JsonResponse(
                {
                    "success": False,
                    "error": "PRTG not configured",
                }
            )

        # Export to PRTG
        result = client.export_device_from_netbox(
            name=name,
            host=host,
        )

        if result.get("success"):
            logger.info(f"Exported {obj_type} '{name}' to PRTG")
        else:
            logger.warning(f"Failed to export {obj_type} '{name}' to PRTG: {result.get('error')}")

        return JsonResponse(result)
