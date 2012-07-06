from london.conf import settings

COOKIE_NAME = getattr(settings, 'SESSION_COOKIE_NAME', 'london_session_key')
STORE_CLASS = getattr(settings, 'SESSION_STORE_CLASS', 'london.apps.sessions.SessionDB')

