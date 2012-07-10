import datetime
import logging
import hashlib

from london.utils.slugs import simplify_special_characters

class BasePool(object):
    def add_message_pool(self, request, message, level=logging.NOTSET):
        # FIXME: shouldn't the name of this method be "add_message_to_pool"?
        raise NotImplementedError('Method "add_message_pool" not implemented')

    def make_message_dict(self, request, message, level=logging.NOTSET):
        level = {
            'info': logging.INFO,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'debug': logging.DEBUG,
            }.get(level, level)

        msg = {
            'level': level,
            'message': message,
            'message_hash': hashlib.md5(simplify_special_characters(message)).hexdigest(),
            'released_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        self.make_id(msg)
        return msg

    def make_id(self, msg):
        msg['id'] = hashlib.md5('%s-%s-%s'%(msg['message'], msg['level'], msg['released_at'])).hexdigest()

    def get_messages(self, request):
        raise NotImplementedError('Method "get_messages" not implemented')

    def delete_message(self, request, message):
        raise NotImplementedError('Method "delete_message" not implemented')

    def get_messages_and_clear(self, request):
        messages = self.get_messages(request)
        for message in messages:
            self.delete_message(message)
        return messages

    def info(self, request, message):
        self.add_message_pool(request, message, logging.INFO)

    def error(self, request, message):
        self.add_message_pool(request, message, logging.ERROR)

    def warning(self, request, message):
        self.add_message_pool(request, message, logging.WARNING)

    def debug(self, request, message):
        self.add_message_pool(request, message, logging.DEBUG)

