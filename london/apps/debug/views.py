from london.templates import render_template
from london.apps.debug import app_settings

@render_template('error_other')
def error_other(request, status_code, status_string, traceback_string='', heap_string='', process_info=None):
    return {
        'request':request,
        'status_code':status_code,
        'status_string':status_string,
        'traceback_string':traceback_string,
        'heap_string':heap_string,
        'process_info':process_info,
        }

@render_template('default_error_404' if app_settings.DEBUG else 'error_404')
def error_404(request, exception, traceback_string, heap_string='', process_info=None):
    return {
        'request':request,
        'exception':exception,
        'traceback_string':traceback_string,
        'heap_string':heap_string,
        'process_info':process_info,
        }

@render_template('default_error_500' if app_settings.DEBUG else 'error_500')
def error_500(request, exception, traceback_string, heap_string='', process_info=None):
    return {
        'request':request,
        'exception':exception,
        'traceback_string':traceback_string,
        'heap_string':heap_string,
        'process_info':process_info,
        }

