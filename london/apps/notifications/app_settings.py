from london.conf import settings

DEFAULT_POOL = getattr(settings, 'NOTIFICATIONS_POOL', 'london.apps.notifications.engines.session.SessionPool')
IN_COOKIES = getattr(settings, 'NOTIFICATIONS_IN_COOKIES', True)
IN_TEMPLATE_CONTEXT = getattr(settings, 'NOTIFICATIONS_IN_TEMPLATE_CONTEXT', False)
IN_AJAX_JSON = getattr(settings, 'NOTIFICATIONS_IN_AJAX_JSON', True)
KEEP_READ_MESSAGES = getattr(settings, 'NOTIFICATIONS_KEEP_READ_MESSAGES', False)
SESSION_KEY = getattr(settings, 'NOTIFICATIONS_SESSION_KEY', '_notifications')
COOKIE_PREFIX = getattr(settings, 'NOTIFICATIONS_COOKIE_PREFIX', '_notifications_')
COOKIE_MAX_AGE = getattr(settings, 'NOTIFICATIONS_COOKIE_MAX_AGE', None)
COOKIE_DOMAIN = getattr(settings, 'NOTIFICATIONS_COOKIE_DOMAIN', None)
COOKIE_PATH = getattr(settings, 'NOTIFICATIONS_COOKIE_PATH', '/')

