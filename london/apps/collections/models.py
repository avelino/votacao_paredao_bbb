from london.db import models
from london.apps.sites.models import Site

class Collection(models.Model):    
    name = models.CharField(max_length=64, unique=True)
    items = models.CharField(max_length=512, blank=True, help_text='app: model: item')
    site = models.ForeignKey(Site, related_name='collections')
    
    def __unicode__(self): 
        return self['name']