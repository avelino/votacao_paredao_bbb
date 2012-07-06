from london.apps.mailing.engines import SmtpEngine

class FakeSmtpEngine(SmtpEngine):
    sent_messages = None

    def __init__(self, *args, **kwargs):
        super(FakeSmtpEngine, self).__init__(*args, **kwargs)
        self.sent_messages = []

    def _send_messages(self, messages):
        self.sent_messages.extend(messages)
        return len(messages)

