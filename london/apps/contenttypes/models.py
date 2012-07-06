from london.db import models
from london.utils.translation import ugettext as _
from london.db.signals import db_post_open
from london.db import _registered_models

class ContentTypeQuerySet(models.QuerySet):
    pass

class ContentType(models.Model):
    class Meta:
        verbose_name = _('Content Type')
        verbose_name_plural = _('Content Types')
        ordering = ('name',)
        unique_together = (('app_label', 'model'),)
        query = 'london.apps.contenttypes.models.ContentTypeQuerySet'

    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(verbose_name=_('python model class name'), max_length=100)

    def __unicode__(self):
        return '%s.%s'%(self['app_label'], self['model'])

    def __repr__(self):
        return '<%s.%s "%s">'%(self._meta.app_label, self.__class__.__name__, unicode(self))

    @classmethod
    def get_for_model(cls, object_or_class):
        if not isinstance(object_or_class, type):
            model = object_or_class.__class__
        else:
            model = object_or_class

        if not issubclass(model, models.Model):
            raise TypeError('Invalid model class for content type: %s'%model)

        return cls.query().get_or_create(
                app_label=model._meta.app_label,
                model=model._meta.model_label,
                defaults={'name': model.__name__},
                )[0]

def update_content_types(connection, **kwargs):
    for cls in _registered_models.values():
        if issubclass(cls, models.Model):
            ContentType.get_for_model(cls)
db_post_open.connect(update_content_types)

