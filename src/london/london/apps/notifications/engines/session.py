import logging

from london.apps.notifications.engines.base import BasePool
from london.apps.notifications.app_settings import SESSION_KEY

class SessionPool(BasePool):
    def add_message_pool(self, request, message, level=logging.NOTSET):
        request.session[SESSION_KEY] = request.session[SESSION_KEY] or []
        request.session[SESSION_KEY].append(self.make_message_dict(request, message, level))
        request.session.modified = True

    def get_messages(self, request):
        return [msg for msg in (request.session[SESSION_KEY] or [])]

    def delete_message(self, request, message):
        request.session.setdefault(SESSION_KEY, [])
        msg_id = message['id']
        for msg in request.session[SESSION_KEY]:
            if msg['id'] == msg_id:
                request.session[SESSION_KEY].remove(msg)
                break
        request.session.modified = True

