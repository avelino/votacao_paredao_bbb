"""
Copied from django-robots ( https://github.com/jezdez/django-robots/ )
Copyright 2009-2011 Jannis Leidel
"""
from london.db import models
from london.apps.sites.models import Site
from london.utils.text import get_text_list

class Url(models.Model):
    """
    Defines a URL pattern for use with a robot exclusion rule. It's 
    case-sensitive and exact, e.g., "/admin" and "/admin/" are different URLs.
    """
    class Meta:
        verbose_name = 'URL'
        verbose_name_plural = 'URLs'

    pattern = models.CharField(max_length=255)

    def __unicode__(self):
        return u"%s" % self['pattern']

    def save(self, *args, **kwargs):
        if not self['pattern'].startswith('/'):
            self['pattern'] = '/' + self['pattern']
        super(Url, self).save(*args, **kwargs)

class Rule(models.Model):
    """
    Defines an abstract rule which is used to respond to crawling web robots,
    using the robot exclusion standard, a.k.a. robots.txt. It allows or 
    disallows the robot identified by its user agent to access the given URLs.
    The Site contrib app is used to enable multiple robots.txt per instance.
    """
    class Meta:
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'

    robot = models.CharField(max_length=255)
    allowed = models.ManyToManyField(Url, blank=True, related_name="allowed")
    disallowed = models.ManyToManyField(Url, blank=True, related_name="disallowed")
    sites = models.ManyToManyField(Site, related_name='rules')
    crawl_delay = models.DecimalField(blank=True, null=True, max_digits=3, decimal_places=1)

    def __unicode__(self):
        return u"%s" % self.robot

    def allowed_urls(self):
        return get_text_list(list(self.allowed.all()), 'and')
    allowed_urls.short_description = 'allowed'

    def disallowed_urls(self):
        return get_text_list(list(self.disallowed.all()), 'and')
    disallowed_urls.short_description = 'disallowed'
    
class AnalyticsQuerySet(models.QuerySet):
    
    def on_site(self):
        site = Site.objects.get_current()
        return site['analytics']
    
class Analytics(models.Model):
    """
    Stores an analytics code like google analytics that can be inserted to the main template
    """
    class Meta:
        verbose_name = 'Analytics code'
        verbose_name_plural = 'Analytics codes'
        query = 'london.apps.seo.models.AnalyticsQuerySet'
        
    name = models.CharField(max_length=255)
    code = models.TextField()
    sites = models.ManyToManyField(Site, related_name='analytics')
    
    def __unicode__(self):
        return self['name']
    
class MetaInfo(models.Model):
    """
    Stores meta descriptions for any stored item (of any app) that have unique URL
    """
    #owner = models.ForeignKey(db_index=True, max_length = 24)
    owner = models.ForeignKey()
    meta_keywords = models.TextField(blank=True)
    meta_description = models.TextField(blank=True)