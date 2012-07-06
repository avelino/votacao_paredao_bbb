from london.db import models

class HashForTags(models.Model):
    hash = models.CharField(max_length=40, unique=True)
    full_path = models.CharField(max_length=500)
    last_inc = models.PositiveIntegerField(blank=True, default=0)

