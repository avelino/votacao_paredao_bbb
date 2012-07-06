from london.conf import settings

STORAGES = getattr(settings, 'CACHE_STORAGES', {
    'default': {
        'engine': 'london.apps.cache.engines.Dummy',
        #'engine': 'london.apps.cache.engines.LocalMemory',
        #'engine': 'london.apps.cache.engines.Redis',
        #'engine': 'london.apps.cache.engines.LocalFileSystem',
        #'path': '/tmp/london-cache/',
        },
    })

DEFAULT_TIMEOUT = getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 60)

