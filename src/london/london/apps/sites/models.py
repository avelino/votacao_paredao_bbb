from urlparse import urljoin
from london.db import models
from london.apps.sites import app_settings
from london.apps.themes.models import Theme

class SiteQuerySet(models.QuerySet):
    
    def active(self):
        return self.filter(is_active=True)
    
class Site(models.Model):
    
    class Meta:
        query = 'london.apps.sites.models.SiteQuerySet'
    
    hostname = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    https_is_default = models.BooleanField(default=False, db_index=True, blank=True)
    is_default = models.BooleanField(default=False, db_index=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True, blank=True)
    theme = models.ForeignKey(Theme, null=True, blank=True, related_name='sites')

    def __unicode__(self):
        return self['name'] or self['domain']

    @property
    def base_url(self):
        scheme = 'http://'

        if self['https_is_default']:
            scheme = 'https://'

        return scheme + self['hostname']

    def format_url(self, url):
        return urljoin(self.base_url, url)

class SiteMirror(models.Model):
    hostname = models.CharField(max_length=50, unique=True)
    site = models.ForeignKey(Site, related_name='mirrors')

    def __unicode__(self):
        return self['hostname']

def detect_current_site(request):
    """Returns the current site according to the request.
    FIXME: this should be in views.py instead of here."""

    site = None
    if app_settings.CURRENT_SITE_BY_HOST_NAME and 'HTTP_HOST' in request.META:
        hostname = request.META['HTTP_HOST'].split(':')[0]
        try:
            site = Site.query().get(hostname=hostname)
        except Site.DoesNotExist:
            try:
                site = SiteMirror.query().get(hostname=hostname)
            except SiteMirror.DoesNotExist:
                pass

    if not site:
        try:
            site = Site.query().filter(is_default=True)[0]
        except IndexError:
            pass

    return site

