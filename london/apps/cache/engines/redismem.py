from london.apps.cache.engines.base import BaseCacheStorage

try:
    import redis
except ImportError:
    redis = None

_connection = None

class Redis(BaseCacheStorage):
    """Simple cache storage to store keys in local memory. Not recommended for production box."""
    host = 'localhost'
    port = 6379
    db = 0

    def __init__(self, **kwargs):
        super(Redis, self).__init__(**kwargs)

        if not redis:
            raise ImportError('Package "redis" is required to use Redis for caching.')

    @property
    def connection(self):
        global _connection
        if not _connection:
            _connection = redis.Redis(host=self.host, port=self.port, db=self.db)
        return _connection

    def set(self, key, value, timeout=None):
        timeout = timeout or self.timeout
        self.connection.set(key, self.serialize(value))

    def get(self, key, default=None):
        value = self.deserialize(self.connection.get(key))
        return value if value is not None else default

    def delete(self, key):
        return self.connection.delete(key)

