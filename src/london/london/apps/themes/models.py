from london.db import models
from london.apps.cache import cache

from registration import list_registered_templates

import app_settings

class Theme(models.Model):
    class Meta:
        ordering = ('verbose_name','name',)
        permissions = (
                ('import_theme', 'Can import Theme'),
                ('download_theme', 'Can download Theme'),
                ('set_default_theme', 'Can set default Theme'),
                )

    name = models.CharField(max_length=50, unique=True)
    verbose_name = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False, db_index=True, blank=True)

    def __unicode__(self):
        return self['verbose_name'] or self['name'] or ('Theme #%s'%self['pk'])

    def create_templates(self):
        """Creates a template instance for every registered templates."""
        for name, params in list_registered_templates():
            if self['templates'].filter(theme=self, name=name).count() == 0:
                self['templates'].create(theme=self, name=name)

    def natural_key(self):
        return (self['name'],)

class ThemeTemplate(models.Model):
    class Meta:
        unique_together = (('theme','name'),)
        ordering = ('name',)

    theme = models.ForeignKey('Theme', related_name='templates')
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    content = models.TextField(blank=True)
    engine = models.CharField(max_length=50, blank=True, help_text='A class path string, like "themes.engines.DjangoTemplate" or "themes.engines.Jinja2Template". If empty, setting THEMES_DEFAULT_ENGINE assumes.')

    def __unicode__(self):
        return self['name']

    def natural_key(self):
        return (self['theme']['name'], self['name'])


class ThemeStaticFile(models.Model):
    class Meta:
        unique_together = (('theme','name'),)
        ordering = ('name',)

    theme = models.ForeignKey('Theme', related_name='static_files')
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='theme-static-files', blank=True, null=True)
    mime_type = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return self['name']

    def get_url(self):
        return self['url'] if self['url'] else self['file'].url

    def get_type(self):
        return 'url' if self['url'] else 'file'

    def natural_key(self):
        return (self['theme']['name'], self['name'])

# SIGNALS
from london.db import signals

def theme_post_save(instance, sender, **kwargs):
    # Sets the other themes "non-default" if this instance is default.
    if instance['is_default']:
        sender.query().exclude(pk=instance['pk']).update(is_default=False)

    # Creates the available templates for this theme
    instance.create_templates()

    # Sets the default name
    if not instance['name']:
        instance['name'] = unicode(instance['pk'])
        instance.save()
signals.post_save.connect(theme_post_save, sender=Theme)

def themetemplate_post_save(instance, sender, **kwargs):
    # Cache invalidation
    cache_key = 'themes:%s|%s'%(instance['theme']['name'], instance['name'])
    if app_settings.CACHE_EXPIRATION and cache.get(cache_key):
        cache.set(cache_key, None, 1) # Expires fastly, to clear cache storage
signals.post_save.connect(themetemplate_post_save, sender=ThemeTemplate)

