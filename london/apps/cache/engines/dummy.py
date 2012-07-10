from london.apps.cache.engines.base import BaseCacheStorage

class Dummy(BaseCacheStorage):
    """Dummy cache storage that does not anything."""

    def set(self, key, value, timeout=None):
        pass

    def get(self, key, default=None):
        return default

    def delete(self, key):
        pass

