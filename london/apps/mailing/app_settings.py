from london.conf import settings

CONNECTIONS = getattr(settings, 'MAILING_CONNECTIONS', {})
DEFAULT_CONTEXT_FUNCTION = getattr(settings, 'MAILING_CONTEXT_FUNCTION', 'london.apps.mailing.schedule_context')
IGNORE_TEST_MODE = getattr(settings, 'MAILING_IGNORE_TEST_MODE', 'london.apps.mailing.engines.SmtpEngine')
STORE_SENT_MESSAGES = getattr(settings, 'MAILING_STORE_SENT_MESSAGES', False)

