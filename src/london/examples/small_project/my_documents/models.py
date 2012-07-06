from london.db import models

class Document(models.Model):
    title = models.CharField()
    content = models.TextField()
    is_published = models.BooleanField()
    extra_infos = models.NestedListField('ExtraInfo', blank=True)

    def __unicode__(self):
        return self['title']

class ExtraInfo(models.NestedModel):
    key = models.CharField()
    value = models.AnyField()

