import os
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

LOCAL = True
DEBUG = LOCAL

SERVICES = {
        'public': {
            'handler': 'london.services.HttpService',
            'urls': 'public.urls',
            'port': 8000,
            }
        }

TEMPLATE_DIRS = (
        os.path.join(ROOT_PATH, 'templates'),
        )

DATABASES = {
        'default': {
            'engine': 'london.db.engines.MongoDB',
            'host': 'localhost',
            'port': 27017,
            'name': 'votacao_bbb',
            }
        }

MIDDLEWARE_CLASSES = (
        'london.apps.seo.middleware.SEOMiddleware',
        'london.apps.debug.middleware.DebugMiddleware',
        'london.apps.sessions.middleware.SessionMiddleware',
        'london.apps.sites.middleware.SiteDetectMiddleware',
        'london.apps.redirects.middleware.RedirectMiddleware',
        'london.apps.auth.middleware.AuthMiddleware',
        'london.apps.themes.middleware.ThemeMiddleware',
        'london.apps.notifications.middleware.NotificationsMiddleware',
        )

TEMPLATE_CONTEXT_PROCESSORS = (
        'london.templates.context_processors.request',
        'london.apps.staticfiles.context_processors.basic',
        'london.apps.auth.context_processors.basic',
        'london.apps.sites.context_processors.basic',
        'london.apps.pagination.context_processors.basic',
        'london.apps.seo.context_processors.basic',
        'london.apps.admin.context_processors.basic',
        'london.apps.notifications.context_processors.basic',
        )

TEMPLATE_LOADERS = (
        'london.apps.themes.loaders.Loader',
        )

INSTALLED_APPS = (
        'london.apps.cache',
        'london.apps.ajax',
        'london.apps.debug',
        'london.apps.seo',
        'london.apps.sessions',
        'london.apps.sites',
        'london.apps.auth',
        'london.apps.admin',
        'london.apps.themes',
        'london.apps.redirects',
        'london.apps.notifications',
        'london.apps.pagination',
        )

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(ROOT_PATH, 'static')

PRINT_TRACEBACK = LOCAL

