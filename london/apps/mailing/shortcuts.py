from london.utils.imports import import_anything
from london.apps.mailing import app_settings
from london.conf import settings

class MailingConnectionNotFound(BaseException): pass

def get_connection(name):
    if name not in app_settings.CONNECTIONS:
        raise MailingConnectionNotFound('Mailing connection "%s" was not found in MAILING_CONNECTIONS setting.' % name)

    engine_class = import_anything(app_settings.CONNECTIONS[name]['engine'])
    kwargs = app_settings.CONNECTIONS[name].copy()
    kwargs.pop('engine')
    return engine_class(**kwargs)

def send_message(engine='default', **kwargs):
    connection = get_connection(engine) if isinstance(engine, basestring) else engine
    message = connection.make_message(**kwargs)
    return message.send()

def send_mailing_schedule(schedule, **kwargs):
    # TODO
    pass

def send_message_to_admins(**kwargs):
    kwargs['to'] = ['%s <%s>'%(name,address) for name,address in settings.ADMINS]
    return send_message(**kwargs)

def send_message_to_managers(**kwargs):
    kwargs['to'] = ['%s <%s>'%(name,address) for name,address in settings.MANAGERS]
    return send_message(**kwargs)

