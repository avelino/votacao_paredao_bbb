"""
Portions of code were copied from Django 1.4 and modified according to London
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""

import smtplib
import socket

from london import forms
from london.apps.mailing.engines.base import BaseEngine
from london.apps.mailing.messages import sanitize_address
from london.apps.mailing.messages import EmailMessage

class SmtpEngine(BaseEngine):
    host = None
    port = None
    user = None
    password = None
    use_tls = False
    subject_prefix = ''
    default_sender = ''

    def __init__(self, configuration=None, host=None, port=None, user=None, password=None, use_tls=None,
            subject_prefix=None, default_sender=None, fail_silently=False, store_sent_messages=None):
        self._configuration = configuration

        if self._configuration:
            self.host = self._configuration['host']
            self.port = self._configuration['port']
            self.user = self._configuration['user']
            self.password = self._configuration['password']
            self.use_tls = self._configuration['use_tls']
            self.subject_prefix = self._configuration['subject_prefix']
            self.default_sender = self._configuration['default_sender']
            self.fail_silently = self._configuration['fail_silently']
            self.store_sent_messages = self._configuration['store_sent_messages']

        self.host = host or self.host
        self.port = port or self.port
        self.user = user or self.user
        self.password = password or self.password
        self.use_tls = use_tls if use_tls is not None else self.use_tls
        self.subject_prefix = subject_prefix or self.subject_prefix
        self.default_sender = default_sender or self.default_sender or self.user
        self.store_sent_messages = store_sent_messages if store_sent_messages is not None else self.store_sent_messages

        super(SmtpEngine, self).__init__(configuration=configuration)

    def configuration_fields(self):
        return [
            ('host',forms.CharField(max_length=50, initial='localhost')),
            ('port',forms.IntegerField(initial=25)),
            ('user',forms.CharField(max_length=50, required=False)),
            ('password',forms.CharField(max_length=50, required=False)),
            ('use_tls',forms.BooleanField(initial=False, required=False)),
            ('subject_prefix',forms.CharField(max_length=50, initial='')),
            ('default_sender',forms.CharField(max_length=50, initial='')),
            ('store_sent_messages',forms.BooleanField(initial=False, required=False)),
            ]

    def open(self):
        from london.apps.mailing.utils import DNS_NAME

        try:
            self._connection = smtplib.SMTP(self.host, self.port, local_hostname=DNS_NAME.get_fqdn())

            if self.use_tls:
                self._connection.ehlo()
                self._connection.starttls()
                self._connection.ehlo()
            if self.user and self.password is not None:
                self._connection.login(self.user, self.password)

            return True
        except:
            if self.fail_silently:
                return False
            raise

    def close(self):
        """Closes the connection to the email server."""
        try:
            try:
                self._connection.quit()
            except socket.sslerror:
                self._connection.close()
            except:
                if not self.fail_silently:
                    raise
        finally:
            self._connection = None

    def _send(self, message):
        """A helper method that does the actual sending."""
        if not message.recipients():
            return False
        from_email = sanitize_address(message.from_email, message.encoding)
        recipients = [sanitize_address(addr, message.encoding)
                      for addr in message.recipients()]
        
        try:
            self._connection.sendmail(from_email, recipients, message.message().as_string())
        except:
            if self.fail_silently:
                return False
            raise
        
        return True

    def make_message(self, **kwargs):
        if kwargs.get('template', None):
            tpl = kwargs['template']
            context = kwargs.get('context', {})
            context['template'] = tpl
            context['site'] = tpl['site']
            kwargs.setdefault('subject', tpl.render_subject(context))
            kwargs.setdefault('body', tpl.render_body(context))

        return EmailMessage(
                connection=self,
                subject=kwargs['subject'],
                body=kwargs['body'],
                from_email=kwargs.get('from_email', self.default_sender),
                to=kwargs['to'],
                cc=kwargs.get('cc', None),
                bcc=kwargs.get('bcc', None),
                attachments=kwargs.get('attachments', None),
                headers=kwargs.get('headers', None),
                )

