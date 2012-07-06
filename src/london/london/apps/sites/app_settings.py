from london.conf import settings

CURRENT_SITE_BY_HOST_NAME = getattr(settings, 'CURRENT_SITE_BY_HOST_NAME', True)
DETECTING_FUNCTION = getattr(settings, 'SITE_DETECTING_FUNCTION', 'london.apps.sites.models.detect_current_site')
INACTIVE_SITE_VIEW = getattr(settings, 'INACTIVE_SITE_VIEW', 'london.apps.sites.views.inactive_site')
ACCEPT_INACTIVE_SITE = getattr(settings, 'ACCEPT_INACTIVE_SITE', True)
MIRROR_PERMANENT_REDIRECT = getattr(settings, 'MIRROR_PERMANENT_REDIRECT', False)
CREATE_SITE_IF_EMPTY = getattr(settings, 'CREATE_SITE_IF_EMPTY', True)

