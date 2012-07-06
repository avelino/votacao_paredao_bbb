from london.conf import settings

APPEND_SLASH = getattr(settings, 'APPEND_SLASH', True)
DEFAULT_EMPTY_FAVICON = getattr(settings, 'DEFAULT_EMPTY_FAVICON', True)
CANONICAL_URL_FUNCTION = getattr(settings, 'CANONICAL_URL_FUNCTION', None)

