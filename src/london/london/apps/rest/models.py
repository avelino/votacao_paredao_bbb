from london.db import models, signals
from london.utils.crypting import get_random_string


class ExternalApplication(models.Model):
    """This is to provide a key to give access to the REST API"""
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    consumer_key = models.CharField(max_length=32, blank=True)
    consumer_secret = models.CharField(max_length=32, blank=True)


def app_pre_save(instance, **kwargs):
    instance['consumer_key'] = instance['consumer_key'] or get_random_string(32)
    instance['consumer_secret'] = instance['consumer_secret'] or get_random_string(32)
signals.pre_save.connect(app_pre_save, sender=ExternalApplication)

