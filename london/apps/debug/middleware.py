import traceback

from london.http import Http404, HttpResponseServerError, HttpResponseNotFound, ErrorHttpResponse
from london.apps.mailing import send_message_to_admins
from london.conf import settings
from london.utils.imports import import_anything
from london.apps.debug.utils import get_process_info, get_memory_heap
from london.utils.logs import get_logger

import app_settings

class DebugMiddleware(object):
    def process_response(self, request, response):
        if isinstance(response, ErrorHttpResponse):
            view_name = app_settings.ERROR_HANDLERS[response.status_code] if response.status_code in app_settings.ERROR_HANDLERS else None
            view = import_anything(view_name) if view_name else import_anything(app_settings.ERROR_HANDLERS['other'])
            response.content = view(request, 
                                    status_code=response.status_code, 
                                    status_string=response.status_string,
                                    traceback_string=traceback.format_exc()).content
        return response
    
    def process_exception(self, request, response, exception):
        logger = get_logger('london')
        full_url = 'http%s://%s%s'%('s' if request.is_secure() else '', request.META['HTTP_HOST'], request.get_full_path())
        exception.name = exception.__class__.__name__

        # Traceback
        tb = traceback.format_exc()

        # Heap
        heap = get_memory_heap()

        # ps info
        process_info = get_process_info()

        if app_settings.PRINT_TRACEBACK:
            msg = []
            msg.append('-'*40)
            msg.append(tb)
            msg.append('-'*40)
            
            if heap:
                msg.append(heap)
                msg.append('-'*40)

            if process_info:
                msg.append(['%s: %s'%(k,v) for k,v in process_info])
                msg.append('-'*40)

            logger.error('\n'.join(msg))

        # URL not found
        if isinstance(exception, Http404):
            if app_settings.PAGE_NOT_FOUND_NOTIFICATION:
                body = [
                    'URL: %s'%full_url,
                    'Headers:',
                    ]
                for k,v in request.META.items():
                    body.append('- %s: %s'%(k,v))

                if request.POST:
                    body.append('POST Data:')
                    for k,v in request.POST.items():
                        body.append('- %s: %s'%(k,v))

                send_message_to_admins(subject='Page not found in the site', body='\n'.join(body))

        else:
            # Error notification
            if not app_settings.DEBUG and app_settings.SERVER_ERROR_NOTIFICATION:
                body = [
                    '%s: %s'%(exception.__class__.__name__, exception),
                    'URL: %s'%full_url,
                    '\nHeaders:',
                    ]
                for k,v in request.META.items():
                    body.append('- %s: %s'%(k,v))

                if request.POST:
                    body.append('\nPOST Data:')
                    for k,v in request.POST.items():
                        body.append(u'- %s: %s' % (k,unicode(v)))

                body.append('\nTraceback:')
                body.append(tb)

                if heap:
                    body.append('\nMemory Heap:')
                    body.append(heap)

                if process_info:
                    body.append('\nProcess Info:')
                    for k,v in process_info:
                        body.append('\n- %s: %s' % (k,v))

                send_message_to_admins(subject='Error in the server', body='\n'.join(body))

        # Response
        if isinstance(exception, Http404):
            view = import_anything(app_settings.ERROR_HANDLERS['404'])
        else:
            view = import_anything(app_settings.ERROR_HANDLERS['500'])

        resp = view(request, exception=exception, traceback_string=tb, heap_string=heap, process_info=process_info)

        if isinstance(exception, Http404):
            return HttpResponseNotFound(resp.content)
        else:
            return HttpResponseServerError(resp.content)

