try:
    import cPickle as pickle
except ImportError:
    import pickle

from london.apps.cache import app_settings

class BaseCacheStorage(object):
    timeout = app_settings.DEFAULT_TIMEOUT

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def set(self, key, value, timeout=60):
        pass

    def get(self, key, default=None):
        pass

    def delete(self, key):
        pass

    def pop(self, key, default=None):
        value = self.get(key, default)
        self.delete(key)
        return value

    def serialize(self, value, fp=None):
        if fp:
            pickle.dump(value, fp, pickle.HIGHEST_PROTOCOL)
        else:
            return pickle.dumps(value, pickle.HIGHEST_PROTOCOL)

    def deserialize(self, value):
        if value is None:
            return None
        elif isinstance(value, basestring):
            return pickle.loads(value)
        else:
            return pickle.load(value)

