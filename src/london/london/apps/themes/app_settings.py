try:
    from london.conf import settings
except ImportError:
    settings = None

# It could be 'jinja2.Template' or any other
DEFAULT_ENGINE = getattr(settings, 'THEMES_DEFAULT_ENGINE', 'jinja2.Template')

BASE_TEMPLATE = getattr(settings, 'THEMES_BASE_TEMPLATE', 'base_themes.html')
AVAILABLE_LOADS = getattr(settings, 'THEMES_AVAILABLE_LOADS', '*') # or a tuple
AVAILABLE_TAGS = getattr(settings, 'THEMES_AVAILABLE_TAGS', '*') # or a tuple
AVAILABLE_FILTERS = getattr(settings, 'THEMES_AVAILABLE_FILTERS', '*') # or a tuple
AVAILABLE_INCLUDES = getattr(settings, 'THEMES_AVAILABLE_INCLUDES', '*') # or a tuple

# Used to block variable from template context processors to ensure security
EXCLUDED_VARIABLES = getattr(settings, 'THEMES_EXCLUDED_VARIABLES', None) # or a tuple

# If True, returns '' instead of TemplateDoesNotExist
STATIC_NOT_FOUND_RETURNS_EMPTY = getattr(settings, 'THEMES_STATIC_NOT_FOUND_RETURNS_EMPTY', False)

# A string with the path of a function to receive the request as argument and return the current
# Theme. This is important to choose which Theme must be used in the request (for instance, the
# developer can use the URL pattern, the host name, or any other criteria for that.
CHOOSING_FUNCTION = getattr(settings, 'THEMES_CHOOSING_FUNCTION', 'london.apps.themes.views.choose_theme')
CURRENT_THEME_COOKIE = getattr(settings, 'THEMES_CURRENT_THEME_COOKIE', '_current_theme')

CACHE_EXPIRATION = getattr(settings, 'THEMES_CACHE_EXPIRATION', 1) #60 * 60 * 24)

ALLOW_NOT_REGISTERED = getattr(settings, 'THEMES_ALLOW_NOT_REGISTERED', False)

