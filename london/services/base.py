import time
import logging
import datetime

from london.exceptions import URLNotFound
from london.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError, Http404
from london.http import WSGIRequest, WebSocketRequest
from london.urls.parsing import resolve_url, resolve_lazy_params
from london.utils.imports import import_anything
from london.conf import settings
from london.utils.logs import get_logger

class BaseService(object):
    name = None
    urls = None
    port = None
    log = None
    host = '0.0.0.0'
    port = 8000
    settings = None
    middleware_classes = None
    log_level = logging.INFO
    log_format = ('%(client_ip)s - "%(method)s %(url)s" %(status)s %(body_length)s %(wall_seconds).6f')

    def __init__(self, urls, host=None, port=None, middleware_classes=None, name=None, log=None, log_format=None,
            log_level=None, settings=None):
        self.urls = urls
        self.host = host or self.host
        self.port = port or self.port
        self.middleware_classes = middleware_classes
        self.name = name
        
        # Log params
        log_params = {}

        self.log = log or self.log
        if self.log: # and isinstance(self.log, basestring):
            #self.log = file(self.log, 'a')
            log_params['filename'] = self.log
            log_params['filemode'] = 'a'
        
        self.log_level = log_level or self.log_level
        self.log_format = log_format or self.log_format
        self.logger = get_logger('london', **log_params)
        self.logger.setLevel(self.log_level)

        # Setting the customized settings
        self.settings = settings or self.settings
        if self.settings:
            self.update_settings()

        self.load_middleware()

    def update_settings(self):
        global settings
        for key,value in self.settings.items():
            setattr(settings.project_settings, key, value)

    def load_middleware(self):
        self._middleware_instances = []

        for path in (self.middleware_classes or settings.MIDDLEWARE_CLASSES):
            cls = import_anything(path)
            inst = cls()
            inst.service = self
            self._middleware_instances.append(inst)

class HttpService(BaseService):
    def request_response(self, request):
        """
        Function to handle client requests, returning a HttpResponse object.
        """

        # Calling middleware methods for request processing before to call the view function
        request._response_middleware = []
        for middleware in self._middleware_instances:
            if hasattr(middleware, 'process_response'):
                request._response_middleware.insert(0, middleware.process_response)

            if hasattr(middleware, 'process_request'):
                resp = middleware.process_request(request)
                if resp is not None:
                    resp.request = request
                    return resp

        try:
            url, args, kwargs = resolve_url(request.path_info[1:], self.urls)

            kwargs.update(url.params)
            #kwargs['request'] = request # Commented to let request argument to be the first no-named arg

            args, kwargs = resolve_lazy_params(request, args, kwargs)
            args = (request,) + args

            resp = url.view(*args, **kwargs)

            if not isinstance(resp, HttpResponse):
                resp = HttpResponse(resp)
        except URLNotFound as e:
            raise Http404(request)

        # Attach the request to the response to keep it in memory, joined
        resp.request = request

        return resp

    def request_handle(self, env, start_response, return_response_object=False):
        """
        Function to encapsulate request_response to return the final content to requester.
        """
        request = WSGIRequest(env, service=self.name)

        try:
            resp = self.request_response(request)

            # Calling middleware methods for response processing
            for func in request._response_middleware:
                new_resp = func(resp.request, resp)
                resp = new_resp or resp
        except BaseException as e:
            # Calls the middleware method 'process_exception'
            resp = None
            for middleware in self._middleware_instances:
                if hasattr(middleware, 'process_exception'):
                    new_resp = middleware.process_exception(request, resp, e)
                    resp = new_resp or resp
                    if resp:
                        break
            if not resp:
                if isinstance(e, Http404):
                    resp = HttpResponseNotFound(request.path_info)
                else:
                    resp = HttpResponseServerError(request.path_info)

        resp.request = request

        if return_response_object:
            return resp

        content = resp.read() # FIXME: this can be improved to be an iterator
        headers = resp.get_headers()

        if content is not None:
            if resp.mime_type and (resp.mime_type.startswith('text/') or resp.mime_type in ('application/javascript','application/json')):
                try:
                    content = content.encode('utf-8')
                except UnicodeDecodeError:
                    pass

            headers = headers + (('Content-Length',len(content)),)
            start_response(resp.get_status(), headers)

            return content
        else:
            start_response(resp.get_status(), headers)

    def get_handle_function(self):
        def handle(env, start_response):
            request_info = {}
            def local_start_response(status, headers):
                request_info['status'] = status
                request_info['headers'] = headers
                return start_response(status, headers)
            request_time = time.time()

            resp = self.request_handle(env, local_start_response)

            response_time = time.time()
            query_string = '?'+env['QUERY_STRING'] if env.get('QUERY_STRING','') else ''
            scheme = 'AJAX' if env.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest' else 'HTTP'
            scheme += 'S' if env.get('HTTPS', False) else ''

            # Logging the request
            self.logger.info(self.log_format % {
                'client_ip': env.get('X_REAL_IP',None) or env['REMOTE_IP'],
                'method': scheme + ' ' + env['REQUEST_METHOD'],
                'url': env.get('PATH_INFO','/') + query_string,
                'status': request_info['status'],
                'body_length': len(resp) if resp else 0,
                'wall_seconds': response_time - request_time,
                })

            return resp
        return handle

class WebSocketService(BaseService):
    port = 9000

    def request_handle(self, ws):
        """
        Function to handle client requests. View must be a class
        """
        request = WebSocketRequest(ws, service=self.name)

        # Calling middleware methods for request processing before to call the view function
        for middleware in self._middleware_instances:
            if hasattr(middleware, 'process_request'):
                resp = middleware.process_request(request)
                #if resp is not None:
                #    return resp

        try:
            url, args, kwargs = resolve_url(request.path_info[1:], self.urls)

            kwargs.update(url.params)
            kwargs['request'] = request

            url.view(*args, **kwargs)
        except URLNotFound:
            resp = HttpResponseNotFound(request.path_info)

            return [resp.content]

    def get_handle_function(self):
        def handle(env, ws):
            return self.request_handle(ws)
        return handle

