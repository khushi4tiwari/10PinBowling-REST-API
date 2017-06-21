from django.db import models

class Match(models.Model):
    """
    Definition of Match object.

    Simply a common reference for multiple Game objects in a multiplayer mode.
    """
    class Meta:
        app_label = 'bowling'
