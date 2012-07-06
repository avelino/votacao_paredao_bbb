import Cookie
import time

from london.conf import settings
from london.services.base import WebSocketService
from london.exceptions import ConnectionClosed

try:
    import gevent
    import gevent.monkey
    import gevent.wsgi
    import gevent.pywsgi
except ImportError:
    gevent = None

try:
    import eventlet
    import eventlet.wsgi
    import eventlet.websocket
except ImportError:
    eventlet = None

try:
    import tornado
    import tornado.httpserver
    import tornado.ioloop
    import tornado.websocket
    from tornado.util import bytes_type as tornado_bytes_type
except ImportError:
    tornado = None

class BaseServer(object):
    service = None

    def __init__(self, service):
        self.service = service

    def run(self):
        raise NotImplementedError('Method "run" must be implemented.')

class GeventServer(BaseServer):
    """Not yet stable enough."""
    if gevent:
        class CustomHandler(gevent.pywsgi.WSGIHandler):
            def get_environ(self):
                env = gevent.pywsgi.WSGIHandler.get_environ(self)
                env['SOCKET'] = self.socket
                env['POST_INPUT'] = env['wsgi.input']
                env['COOKIES'] = Cookie.SimpleCookie(env.get('HTTP_COOKIE',''))
                return env
    else:
        CustomHandler = None

    def __init__(self, service):
        if not gevent:
            raise ImportError('To use Gevent server you must have Gevent installed.')

        # Monkey patching is a good idea but raises conflicts with PyMongo connection
        #gevent.monkey.patch_socket()
        super(GeventServer, self).__init__(service)

    def run(self):
        """
        Responsible for spawning a WSGI server.
        """

        self.server = gevent.pywsgi.WSGIServer((self.service.host, self.service.port),
                self.service.get_handle_function(), log=self.service.log,
                handler_class=self.CustomHandler) # SSL: keyfile='path', certfile='path'

        # Non-blocking server starter should be self.server.start(). To run blocking, call:
        self.server.serve_forever()

class EventletServer(BaseServer):
    def __init__(self, service):
        if not eventlet:
            raise ImportError('To use Eventlet server you must have eventlet installed.')

        # Monkey patching is a good idea but raises conflicts with PyMongo connection
        #eventlet.monkey_patch()
        super(EventletServer, self).__init__(service)

    def run(self):
        """
        Responsible for spawning a WSGI server.
        """
        self.listening = eventlet.listen(('', self.service.port))

        if isinstance(self.service, WebSocketService):
            @eventlet.websocket.WebSocketWSGI
            def internal_function(ws):
                ws.environ['SOCKET'] = ws.environ['eventlet.input'].get_socket()
                ws.environ['POST_INPUT'] = '' # FIXME: ws.environ['wsgi.input'].read()
                ws.environ['COOKIES'] = Cookie.SimpleCookie(ws.environ.get('HTTP_COOKIE',''))
                ws.environ['REMOTE_IP'] = '' # FIXME
                return self.service.get_handle_function()(ws)
        else:
            def internal_function(env, start_response):
                env['SOCKET'] = env['eventlet.input'].get_socket()
                env['POST_INPUT'] = env['wsgi.input']
                env['COOKIES'] = Cookie.SimpleCookie(env.get('HTTP_COOKIE',''))
                env['REMOTE_IP'] = '' # FIXME
                return self.service.get_handle_function()(env, start_response)

        eventlet.wsgi.server(self.listening, internal_function, log=False, #self.service.log,
                debug=settings.DEBUG)

class TornadoServer(BaseServer):
    def __init__(self, service):
        if not tornado:
            raise ImportError('To use Tornado server you must have tornado installed.')

        super(TornadoServer, self).__init__(service)

    def make_env(self, request):
        env = dict([(k.upper().replace('-','_'),v) for k,v in request.headers.items()])
        env['PATH_INFO'] = request.uri.split('?',1)[0]
        env['HTTP_X_REQUESTED_WITH'] = env.get('X_REQUESTED_WITH', None)
        env['REQUEST_METHOD'] = request.method
        class Stream(object):
            def read(self, *args, **kwargs):
                return request.body
        env['POST_INPUT'] = Stream()
        env['COOKIES'] = request.cookies
        env['SOCKET'] = request.connection.stream.socket
        env['HTTP_HOST'] = request.host

        def async_write(data):
            try:
                request.connection.stream.write(data)
            except IOError:
                raise ConnectionClosed('Connection was closed. This cannot be written: %s' % data)
        env['ASYNC_WRITE'] = async_write

        def set_async_request(value=True):
            request.is_asynchronous = value
        env['FUNCTION_SET_ASYNC'] = set_async_request

        def connection_closed():
            return request.connection._request_finished
        env['FUNCTION_CLOSED'] = connection_closed

        def async_timeout(seconds, func, *args, **kwargs):
            tornado.ioloop.IOLoop.instance().add_timeout(time.time() + seconds, lambda:func(*args,**kwargs))
        env['ASYNC_TIMEOUT'] = async_timeout

        def finish():
            try:
                request.finish()
            except (IOError, AssertionError):
                pass
        env['FUNCTION_FINISH'] = finish
        env['REMOTE_IP'] = request.remote_ip
        env['QUERY_STRING'] = request.query

        return env

    def run(self):
        def http_handler(request):
            env = self.make_env(request)

            def write(block):
                # Encode bytes block through latin1 to avoid assertation error in Tornado
                if tornado_bytes_type is str and isinstance(block, unicode):
                    block = block.encode('latin1')
                
                request.write(block)

            def start_response(status, headers):
                write("HTTP/1.1 %s\r\n"%status)
                for k,v in headers:
                    write("%s: %s\r\n"%(k, v))

            handler_function = self.service.get_handle_function()
            content = handler_function(env, start_response) or ''
            if not getattr(request, 'is_asynchronous', False):
                write("\r\n%s"%content)
                request.finish()

        self.http_server = tornado.httpserver.HTTPServer(http_handler)
        self.http_server.listen(self.service.port)
        tornado.ioloop.IOLoop.instance().start()

