from london.db import models, signals
from london.utils.slugs import slugify

class Category(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self['name']

class Style(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self['name']


class Product(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=40)
    slug = models.SlugField(unique=True)
    styles = models.ManyToManyField(Style)
    category = models.ForeignKey(Category)
    tags = models.ListField()

    def __unicode__(self):
        return self['name']


# SIGNALS

def category_pre_save(instance, **kwargs):
    instance['slug'] = instance['slug'] or slugify(instance['name'])
signals.pre_save.connect(category_pre_save, sender=Category)

def style_pre_save(instance, **kwargs):
    instance['slug'] = instance['slug'] or slugify(instance['name'])
signals.pre_save.connect(style_pre_save, sender=Style)

def product_pre_save(instance, **kwargs):
    instance['slug'] = instance['slug'] or slugify(instance['name'])
signals.pre_save.connect(product_pre_save, sender=Product)

