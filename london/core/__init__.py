from london.conf import settings
from london.utils.imports import import_anything
from london.exceptions import ApplicationNotFound

_installed_apps = None
def load_apps():
    """Loads installed applications to load everything they have in their __init__.py"""
    global _installed_apps

    if not _installed_apps:
        _installed_apps = []
        for app_name in settings.INSTALLED_APPS:
            _installed_apps.append(get_app(app_name))
    return _installed_apps

def get_app(name):
    """Returns application module for a given name"""
    try:
        entry = settings.INSTALLED_APPS[name]
        path = entry if isinstance(entry, basestring) else entry[0]
        mod = import_anything(path)
        mod._app_in_london = name
        mod._installed_entry = entry

        try:
            mod._models = import_anything('models', mod)
        except ImportError:
            mod._models = None

        return mod
    except (ImportError, KeyError):
        raise ApplicationNotFound('Application "%s" was not found.'%name)

