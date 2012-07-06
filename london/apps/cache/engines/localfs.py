import os
import datetime
from london.apps.cache.engines.base import BaseCacheStorage

class LocalFileSystem(BaseCacheStorage):
    """Simple cache storage to store keys in local file system."""

    def get_file_path(self, key):
        return os.path.join(self.path, str(key)[:5], key)

    def get_file(self, key, mode='r'):
        file_path = self.get_file_path(key)
        if not os.path.exists(os.path.split(file_path)[0]):
            os.makedirs(os.path.split(file_path)[0])
        return file(file_path, mode)

    def set(self, key, value, timeout=None):
        timeout = timeout or self.timeout
        expires = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

        fp = self.get_file(key, 'w')
        self.serialize([expires, value], fp)
        fp.close()

    def get(self, key, default=None):
        if not os.path.exists(self.get_file_path(key)):
            return default

        fp = self.get_file(key)
        expires, value = self.deserialize(fp)
        fp.close()

        if datetime.datetime.now() > expires:
            self.delete(key)
            return default

        return value

    def delete(self, key):
        if os.path.exists(self.get_file_path(key)):
            os.unlink(self.get_file_path(key))

