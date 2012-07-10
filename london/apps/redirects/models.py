from london.db import models
from london.apps.sites.models import Site

class Redirect(models.Model):
    """
    URL pattern field supports regular expression and URL destination field supports $1, $2, etc.
    """
    url_pattern = models.CharField(max_length=100)
    url_destination = models.CharField(max_length=100)
    site = models.ForeignKey(Site, related_name='redirects')
    is_permanent = models.BooleanField(default=False, blank=True)

    def __unicode__(self):
        return self['url_pattern']


