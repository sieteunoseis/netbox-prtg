"""
Forms for NetBox PRTG plugin settings.
"""

from django import forms


class PRTGSettingsForm(forms.Form):
    """Form for displaying PRTG plugin configuration."""

    prtg_url = forms.URLField(
        required=False,
        label="PRTG Server URL",
        help_text="Full URL to PRTG server (e.g., https://prtg.example.com)",
        widget=forms.URLInput(attrs={"class": "form-control", "readonly": True}),
    )

    prtg_api_token = forms.CharField(
        required=False,
        label="API Token",
        help_text="API token from PRTG account settings",
        widget=forms.PasswordInput(attrs={"class": "form-control", "readonly": True}),
    )

    timeout = forms.IntegerField(
        required=False,
        label="Timeout (seconds)",
        help_text="API request timeout in seconds",
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )

    cache_timeout = forms.IntegerField(
        required=False,
        label="Cache Timeout (seconds)",
        help_text="How long to cache API responses",
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
    )

    verify_ssl = forms.BooleanField(
        required=False,
        label="Verify SSL",
        help_text="Verify SSL certificates when connecting to PRTG",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": True}),
    )
