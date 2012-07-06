from london.conf import settings
from london.utils.imports import import_anything
from london.db import _registered_models

def get_related_class(field, obj):
    """Returns a model class that is related by a field in a given object.""" 
    related = field.related

    if not isinstance(obj, type):
        cls = obj.__class__
    else:
        cls = obj

    if hasattr(related, '_meta'):
        return related
    elif '.' not in related:
        return get_model('%s.%s'%(cls._meta.app_label, related))
    else:
        return get_model(related)

def get_model(path):
    """Returns the model class for a given path in "app.Model" format."""
    try:
        return import_anything(path)
    except ImportError:
        pass

    path = '.'.join(path.split('.', 1)[-2:])
    if path in _registered_models:
        return _registered_models[path]
    else:
        raise ImportError('Model "%s" was not found.'%path)

