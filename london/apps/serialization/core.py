import app_settings
from london.utils.imports import import_anything

def serialize(obj, serializer=app_settings.DEFAULT_SERIALIZER):
    serializer = get_serializer(serializer)
    return serializer.serialize(obj)

def deserialize(data, serializer=app_settings.DEFAULT_SERIALIZER):
    serializer = get_serializer(serializer)
    return serializer.deserialize(data)

def get_serializer(serializer=app_settings.DEFAULT_SERIALIZER):
    if isinstance(serializer, basestring):
        serializer = import_anything(serializer)
    if isinstance(serializer, type):
        serializer = serializer()
    return serializer

