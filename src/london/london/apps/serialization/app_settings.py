from london.conf import settings

DEFAULT_SERIALIZER = getattr(settings, 'DEFAULT_SERIALIZER', 'london.apps.serialization.JsonSerializer')

