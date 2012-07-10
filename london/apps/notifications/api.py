from london.utils.imports import import_anything
from london.conf import settings

_pool = None
def get_pool():
    """Returns the instance of the current notifications pool in the system. It is able to recognize the setting was changed
    and then to create a new instance for the new class."""
    global _pool

    if getattr(settings, 'NOTIFICATIONS_POOL', None):
        pool_path = settings.NOTIFICATIONS_POOL
    else:
        from london.apps.notifications import app_settings
        pool_path = app_settings.DEFAULT_POOL

    if not _pool or _pool._string_setting != pool_path:
        _pool = import_anything(pool_path)()
        _pool._string_setting = pool_path
    return _pool

def get_messages(request):
    return get_pool().get_messages(request)

def get_messages_and_clear(request):
    return get_pool().get_messages_and_clear(request)

def delete_message(request, message):
    return get_pool().delete_message(request, message)

def info(request, message):
    return get_pool().info(request, message)

def error(request, message):
    return get_pool().error(request, message)

def warning(request, message):
    return get_pool().warning(request, message)

def debug(request, message):
    return get_pool().debug(request, message)

