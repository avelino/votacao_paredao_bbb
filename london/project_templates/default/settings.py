import os
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

LOCAL = True
DEBUG = True

SERVICES = {
        'public': {
            'handler': 'london.services.HttpService',
            'urls': 'public.urls',
            'port': 8000,
            },
        }

TEMPLATE_DIRS = (
        os.path.join(ROOT_PATH, 'templates'),
        )

DATABASES = {
        'default': {
            'engine': 'london.db.engines.MongoDB',
            'host': 'localhost',
            'port': 27017,
            'name': 'database_name_to_replace',
            }
        }

MIDDLEWARE_CLASSES = (
        #'london.apps.seo.middleware.SEOMiddleware',
        #'london.apps.debug.middleware.DebugMiddleware',
        #'london.apps.sessions.middleware.SessionMiddleware',
        #'london.apps.auth.middleware.AuthMiddleware',
        #'london.apps.themes.middleware.ThemeMiddleware',
        #'london.apps.sites.middleware.SiteDetectMiddleware',
        #'london.apps.notifications.middleware.NotificationsMiddleware',
        )

TEMPLATE_CONTEXT_PROCESSORS = (
        'london.apps.staticfiles.context_processors.basic',
        #'london.templates.context_processors.request',
        #'london.apps.auth.context_processors.basic',
        #'london.apps.sites.context_processors.basic',
        #'london.apps.pagination.context_processors.basic',
        #'london.apps.seo.context_processors.basic',
        #'london.apps.notifications.context_processors.basic',
        #'london.apps.admin.context_processors.basic',
        )

TEMPLATE_LOADERS = (
        'london.apps.themes.loaders.Loader',
        )

INSTALLED_APPS = {
        'staticfiles': 'london.apps.staticfiles',
        'themes': 'london.apps.themes',
        #'mailing': 'london.apps.mailing',
        #'cache': 'london.apps.cache',
        #'ajax': 'london.apps.ajax',
        #'debug': 'london.apps.debug',
        #'seo': 'london.apps.seo',
        #'sessions': 'london.apps.sessions',
        #'sites': 'london.apps.sites',
        #'auth': 'london.apps.auth',
        #'admin': 'london.apps.admin',
        #'redirects': 'london.apps.redirects',
        #'notifications': 'london.apps.notifications',
        #'pagination': 'london.apps.pagination',
        #'my_documents': 'my_documents',
        }

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(ROOT_PATH, 'static')
UPLOADS_URL = '/static/uploads/'
UPLOADS_ROOT = os.path.join(STATIC_ROOT, 'uploads')

