"""
Application responsible for the mailing, which includes mainly sending e-mails via SMTP, but supporting as well extending to support
other protocols in order to send push notifications, SMS, Twitter, XMPP, among others.

This application is able as well to allow the user to construct mail templates and automated e-mail sending, as such as allow the
connection configurations be set and changed via administration site instead of having to change the source code. Which means the
users can set the mail configurations by themselves.
"""

from london.apps.mailing.shortcuts import send_message, send_mailing_schedule
from london.apps.mailing.shortcuts import send_message_to_admins, send_message_to_managers

def schedule_context():
    return {}

