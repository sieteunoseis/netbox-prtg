from django.db import models


class Prtg(models.Model):
    """Unmanaged model to register custom permissions for the PRTG plugin."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("configure_prtg", "Can configure PRTG plugin settings"),
        )
