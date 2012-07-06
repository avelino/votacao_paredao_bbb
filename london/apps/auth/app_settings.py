from london.conf import settings

LOGIN_URL = getattr(settings, 'LOGIN_URL', None)
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
PASSWORD_RESET_TIMEOUT_DAYS = getattr(settings, 'PASSWORD_RESET_TIMEOUT_DAYS', 5)
PASSWORD_RESET_SEND_TOKEN = getattr(settings, 'PASSWORD_RESET_SEND_TOKEN', 'london.apps.auth.views.send_token')
DISABLE_DEFAULT_AUTHENTICATION = getattr(settings, 'DISABLE_DEFAULT_AUTHENTICATION', False)

