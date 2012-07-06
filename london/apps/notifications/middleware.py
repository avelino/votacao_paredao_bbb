try:
    import json as simplejson
except ImportError:
    import simplejson

import logging

from london.apps.notifications import app_settings
from london.apps.notifications.api import get_messages, delete_message, info, warning, error, debug
from london.http import JsonResponse, HttpResponse

class NotificationsMiddleware(object):
    def process_request(self, request):
        """Attaching proxy methods to notification functions."""
        request.info = lambda msg: info(request, msg)
        request.warning = lambda msg: warning(request, msg)
        request.error = lambda msg: error(request, msg)
        request.debug = lambda msg: debug(request, msg)

    def process_response(self, request, response):
        if not app_settings.IN_COOKIES and not app_settings.IN_AJAX_JSON:
            return response

        messages = get_messages(request)

        # Sends notifications as cookies
        if messages:
            if app_settings.IN_COOKIES and not request.is_ajax():
                for msg in messages:
                    cookie_name = app_settings.COOKIE_PREFIX + unicode(msg['id'])
                    if cookie_name not in request.COOKIES:
                        response.set_cookie(
                            str(cookie_name),
                            '%s:%s:%s:%s'%(
                                logging._levelNames[msg['level']].lower(),
                                msg['message_hash'],
                                msg['released_at'],
                                msg['message'],
                                ),
                            max_age=app_settings.COOKIE_MAX_AGE,
                            domain=app_settings.COOKIE_DOMAIN,
                            path=app_settings.COOKIE_PATH,
                            )

                    if not app_settings.KEEP_READ_MESSAGES:
                        delete_message(request, msg)
            elif app_settings.IN_AJAX_JSON and request.is_ajax():
                content = response.content.content if isinstance(response.content, HttpResponse) else response.content
                if isinstance(content, dict):
                    content['_notifications'] = []
                    for msg in messages:
                        if msg['level'] in logging._levelNames:
                            level = logging._levelNames[msg['level']].lower()
                        else:
                            level = msg['level'].lower()

                        content['_notifications'].append({
                            'id': msg['id'],
                            'level': level,
                            'message': msg['message'],
                            'message_hash': msg['message_hash'],
                            'released_at': msg['released_at'],
                            })

                        if not app_settings.KEEP_READ_MESSAGES:
                            delete_message(request, msg)

        return response

