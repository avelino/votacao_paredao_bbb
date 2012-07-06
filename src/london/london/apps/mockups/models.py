import datetime

from london.db import models
import app_settings

class MockupView(models.Model):
    url_pattern = models.CharField(max_length=150)
    creation = models.DateTimeField(default=datetime.datetime.now, blank=True)
    status_code = models.PositiveSmallIntegerField(default=200, blank=True)
    mime_type = models.CharField(max_length=100, default='text/html', blank=True)
    headers = models.TextField(blank=True)
    content = models.TextField(blank=True)
    raw_file = models.FileField(upload_to=app_settings.FILES_UPLOAD_TO, blank=True, null=True)
    python_code = models.TextField(blank=True)
    force_https = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=False, blank=True, db_index=True)

    def __unicode__(self):
        return self.url_pattern

