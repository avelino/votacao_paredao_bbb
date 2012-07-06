import sys
import os

ADMINS = MANAGERS = ()

TEMPLATE_CONTEXT_PROCESSORS = (
        'london.templates.context_processors.request',
        'london.apps.staticfiles.context_processors.basic',
        'london.apps.auth.context_processors.basic',
        'london.apps.sites.context_processors.basic',
        'london.apps.pagination.context_processors.basic',
        'london.apps.seo.context_processors.basic',
        'london.apps.collections.context_processors.basic',
        'london.apps.notifications.context_processors.basic',
        )

TEMPLATE_EXTENSIONS = (
        'london.templates.jinja_extensions.LondonExtension',
        'london.apps.ajax.AjaxExtension', # FIXME: This coupling is not good, we have to find a better way for this.
        'london.apps.i18n.I18nExtension',
        'london.apps.seo.SeoExtension',
        'london.apps.themes.ThemeExtension',
        'jinja2.ext.autoescape',
        #'jinja2.ext.i18n',
        )

TEMPLATE_FILTERS = (
        'london.templates.defaultfilters',
        )

DEFAULT_ENCRYPT_ALGORITHM = 'sha1'

TEMP_DIR = os.environ.get('TEMP', 'c:/windows/temp/') if sys.platform == 'win32' else '/tmp/'

MIDDLEWARE_CLASSES = (
        )

TEMPLATE_LOADERS = (
        )

LOCAL = True

USE_L10N = True
USE_I18N = True
LANGUAGE_CODE = 'en-gb'
FORMAT_MODULE_PATH = 'formats'
DATE_INPUT_FORMATS = ('%d/%m/%Y', '%Y-%m-%d', '%d/%m', 'today', '%d', '%n days', '%nd', '%a', '%A')
TIME_INPUT_FORMATS = ('%H:%M', '%H:%M:%S', 'now', '%H', '%n min', '%n hour',)
DATETIME_INPUT_FORMATS = ('%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S')
DECIMAL_SEPARATOR = '.'
DECIMAL_PLACES = 2
NUMBER_GROUPING = 3
THOUSAND_SEPARATOR = ','
USE_THOUSAND_SEPARATOR = True

SECRET_KEY = 'PleaseDontUseThisSecretKey'

DEFAULT_CONTENT_TYPE = 'text/html'
DEFAULT_CHARSET = 'utf-8'
FILE_UPLOAD_HANDLERS = (
    'london.core.files.uploadhandler.MemoryFileUploadHandler',
    'london.core.files.uploadhandler.TemporaryFileUploadHandler',
)
# Maximum size, in bytes, of a request before it will be streamed to the
# file system instead of into memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 # i.e. 2.5 MB
DEFAULT_FILE_STORAGE = 'london.core.files.storage.FileSystemStorage'

# The numeric mode to set newly-uploaded files to. The value should be a mode
# you'd pass directly to os.chmod; see http://docs.python.org/lib/os-file-dir.html.
FILE_UPLOAD_PERMISSIONS = None

FILE_UPLOAD_TEMP_DIR = None

DEFAULT_CURRENCY = 'GBP'

REQUIRED_PACKAGES = []

COMMANDS_MODULES = None

UPLOADS_URL = None
UPLOADS_ROOT = None

# CORS related settings
CORS_ALLOWED_ORIGINS = None # List or tuple are expected in this setting
CORS_ALLOWED_CREDENTIALS = False # Boolean for including cookies in cross domain permission

TEST_ADDITIONAL_ARGS = ['--doctest-extension=txt',]
TEST_DEFAULT_APPS = None

