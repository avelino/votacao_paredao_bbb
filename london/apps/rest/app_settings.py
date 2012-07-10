from london.conf import settings

EXTERNAL_APPLICATION_AUTH = getattr(settings, 'REST_EXTERNAL_APPLICATION_AUTH', False)
CACHE_KEY_PREFIX = getattr(settings, 'REST_SEARCH_CACHE_KEY_PREFIX', 'rest-search-')
CACHE_TIMEOUT = getattr(settings, 'REST_SEARCH_CACHE_TIMEOUT', 60 * 5) # 5 minutes

