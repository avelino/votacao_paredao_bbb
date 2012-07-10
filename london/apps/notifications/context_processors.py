from london.apps.notifications import app_settings
from london.apps.notifications.api import get_messages_and_clear

def basic(request):
    ret = {'notifications_cookie_prefix':app_settings.COOKIE_PREFIX}
    if app_settings.IN_TEMPLATE_CONTEXT:
        ret['notifications'] = get_messages_and_clear(request)
    return ret
