import threading

from london.apps.mailing import app_settings, signals

class BaseEngine(object):
    fail_silently = False
    store_sent_messages = app_settings.STORE_SENT_MESSAGES

    def __init__(self, configuration=None):
        self._configuration = configuration
        self._lock = threading.RLock()

    def open(self):
        pass

    def close(self):
        pass

    def configuration_fields(self):
        return []

    def make_message(self, **kwargs):
        raise NotImplementedError

    def send_messages(self, messages):
        # This import is here to ensure the settings was already changed by the test command
        from london.conf import settings

        if getattr(settings, '_TESTING', None) or not app_settings.IGNORE_TEST_MODE:
            from london.apps import mailing
            mailing.test_sent_messages = getattr(mailing, 'test_sent_messages', [])
            mailing.test_sent_messages.extend(messages)
            return len(messages)

        return self._send_messages(messages)

    def _send_messages(self, messages):
        if not messages:
            return

        self._lock.acquire()
        try:
            self.open()

            sent = 0
            for message in messages:
                sent = self.send(message)
                if sent:
                    sent += 1

            self.close()
        finally:
            self._lock.release()

        return sent

    def send(self, message):
        signals.pre_send.send(sender=self, message=message)
        sent = self._send(message)
        signals.post_send.send(sender=self, message=message, success=bool(sent))

        return sent

    def _send(self, message):
        raise NotImplementedError

