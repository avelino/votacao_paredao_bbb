from london.db import models

SEAWALL = ((1, u'XXX'),
        (2, u'YYY'))


class Votes(models.Model):
    result = models.CharField(choices=SEAWALL)

    def __unicode__(self):
        return self['result']
