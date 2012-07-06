import datetime

from london.db import models
from london.apps.sites.models import Site
from london.apps.mailing import app_settings, signals
from london.utils.imports import import_anything

from jinja2 import Template

class MailingConfiguration(models.Model):
    """
    Model class to store mailing configurations, like SMTP account, etc.
    Configuration fields, like SMTP host, user, password, TLS, etc. must be defined by the backend
    """
    name = models.CharField(max_length=50, unique=True)
    is_enabled = models.BooleanField(default=True, blank=True)
    backend = models.CharField(max_length=100, default=None)
    site = models.ForeignKey(Site, blank=True, null=True)

    def get_backend(self):
        return import_anything(self['backend'])(configuration=self)

class MessageTemplate(models.Model):
    """
    Template to be used when sending mail message
    """
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=100, blank=True)
    body = models.TextField(blank=True)
    recipients = models.ListField(blank=True, null=True)
    site = models.ForeignKey(Site, blank=True, null=True, related_name='message_templates')

    def render_subject(self, context=None):
        context = context or {}
        tpl = Template(self['subject'])
        return tpl.render(**context).strip()

    def render_body(self, context=None):
        context = context or {}
        tpl = Template(self['body'])
        return tpl.render(**context).strip()

class SentMessage(models.Model):
    """
    Sent messsage log.

    Additional fields come from each backend
    """
    date_sent = models.DateTimeField(default=datetime.datetime.now, blank=True)
    configuration = models.ForeignKey(MailingConfiguration)
    site = models.ForeignKey('sites.Site', blank=True, null=True)
    related_to = models.ListField(blank=True, null=True)

class MailingSchedule(models.Model):
    """
    Model class for mail sending schedule

    Time fields work with the same syntax of Crontab fields, example:
    minute    hour    day_of_month    month    day_of_week
    0-59/5    10      *               *        *

    Context function is the string path for the function to get the context keys and values
    """
    time_fields = models.CharField(max_length=50, blank=True, default='*')
    template = models.ForeignKey(MessageTemplate)
    configuration = models.ForeignKey(MailingConfiguration)
    context_function = models.CharField(max_length=100, default=app_settings.DEFAULT_CONTEXT_FUNCTION, blank=True)

def store_sent_message_in_database(message, **kwargs):
    if message.connection.store_sent_messages:
        sent_message = SentMessage()
        sent_message['configuration'] = getattr(message, 'configuration', None)
        for name, value in message.get_fields_to_store().items():
            sent_message[name] = value
        sent_message.save()
signals.post_send.connect(store_sent_message_in_database)

