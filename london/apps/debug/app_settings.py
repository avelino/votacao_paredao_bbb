import sys
import warnings
from london.conf import settings

DEBUG = getattr(settings, 'DEBUG', True)
PAGE_NOT_FOUND_NOTIFICATION = getattr(settings, 'PAGE_NOT_FOUND_NOTIFICATION', False)
SERVER_ERROR_NOTIFICATION = getattr(settings, 'SERVER_ERROR_NOTIFICATION', True)

DEFAULT_ERROR_HANDLERS = {
    '404': 'london.apps.debug.views.error_404',
    '500': 'london.apps.debug.views.error_500',
    'other': 'london.apps.debug.views.error_other'
}
                           
ERROR_HANDLERS = getattr(settings, 'ERROR_HANDLERS', DEFAULT_ERROR_HANDLERS)

PRINT_TRACEBACK = getattr(settings, 'PRINT_TRACEBACK', False)
SEND_PROCESS_INFO = getattr(settings, 'DEBUG_PROCESS_INFO', False)
SEND_MEMORY_HEAP = getattr(settings, 'DEBUG_MEMORY_HEAP', False)

if sys.platform == 'win32' and SEND_PROCESS_INFO:
    warnings.warn('Windows platform usually has not command "ps" for getting process information.', Warning)

