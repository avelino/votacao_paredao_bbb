"""
This application is responsible for different levels of caching, including:

    - server side caching (usually using memory, database, file system or cache engines like Memcache and Redis
    - browser site caching control, like E-Tag, Conditional, Expiration and others

For server side caching, this application supports more than one connection, intermidiated by a proxy object that allows
other applications to store and retrieve cached information to boost the performance, improve the scalability (distributing
cached values) and save system resources.
"""

from london.utils.imports import import_anything

class CacheProxy(object):
    """This class can work as a dictionary, specifying a key to work with a specific storage instead of the default one."""
    storages = None

    def __init__(self, storages=None):
        self.storages = storages

    def load_storage(self, conf):
        # Loads default storages if not specific
        if not self.storages:
            import app_settings
            self.storages = app_settings.STORAGES

        # Supports reference by string key
        if isinstance(conf, basestring):
            conf = self.storages[conf]

        # Creates the instance if a configuration dict was given
        if isinstance(conf, dict):
            cls = import_anything(conf['engine'])
            kwargs = {}
            kwargs.update(conf)
            kwargs.pop('engine')
            return cls(**kwargs)

        return conf

    def __getitem__(self, key):
        return self.load_storage(key)

    def __setitem__(self, key, value):
        self.storages[key] = self.load_storage(value)

    def __delitem__(self, key, value):
        if self.storages:
            del self.storages[key]

    def set(self, key, value, timeout=None):
        return self['default'].set(key, value, timeout)

    def get(self, key, default=None):
        return self['default'].get(key, default)

    def delete(self, key):
        return self['default'].delete(key)

    def pop(self, key, default=None):
        return self['default'].pop(key, default)

# Loads cache storages
cache = CacheProxy()

