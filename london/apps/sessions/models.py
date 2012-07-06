import datetime
from london.db import models

class Session(models.Model):
    creation = models.DateTimeField(default=datetime.datetime.now, blank=True)

    def items(self):
        items = {}
        items.update(self._old_values)
        items.update(self._new_values)
        return items.items()

