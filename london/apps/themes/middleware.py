from london.utils.imports import import_anything
from london.exceptions import ImproperlyConfigured

import app_settings
from models import Theme

class ThemeMiddleware(object):
    """Sets the current theme."""

    def process_request(self, request):
        if app_settings.CHOOSING_FUNCTION:
            try:
                path, func_name = app_settings.CHOOSING_FUNCTION.rsplit('.', 1)
            except ValueError:
                raise ImproperlyConfigured("Setting THEMES_CHOOSING_FUNCTION has '%s' with a unknown function path."%app_settings.CHOOSING_FUNCTION)

            try:
                mod = import_anything(path)
            except ImportError:
                raise ImproperlyConfigured("Module '%s' wasn't found."%path)

            try:
                func = getattr(mod, func_name)
            except AttributeError:
                raise ImproperlyConfigured("Module '%s' hasn't a function called."%func_name)

            request.theme = func(request)

        if not getattr(request, 'theme', None):
            if getattr(request, 'site', None) and request.site['theme']:
                request.theme = request.site['theme']
            else:
                try:
                    request.theme = Theme.query().get(is_default=True)
                except Theme.DoesNotExist:
                    request.theme = None

