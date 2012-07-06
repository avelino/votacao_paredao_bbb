import datetime
from london.apps.cache.engines.base import BaseCacheStorage

_store = {}

class LocalMemory(BaseCacheStorage):
    """Simple cache storage to store keys in local memory. Not recommended for production box."""
    def set(self, key, value, timeout=None):
        timeout = timeout or self.timeout
        expires = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        _store[key] = (value, expires)

    def get(self, key, default=None):
        try:
            value, expires = _store[key]
        except KeyError:
            return default

        if datetime.datetime.now() > expires:
            del _store[key]
            return default

        return value

    def delete(self, key):
        if key in _store:
            del _store[key]

