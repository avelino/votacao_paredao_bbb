"""
Used to work stable, but is frozen at the moment because of regular changes in W3C's WebSocket protocol.
"""
import socket

try:
    import json as simplejson
except ImportError:
    import simplejson

from london.utils.json_encoding import CustomJSONEncoder
from london.http import HttpResponseBadRequest, HttpVersionNotSupported

def websocket(func):
    """
    Decorator for WebSocket views. Just declare a function like this:

    @websocket
    def my_websocket_handler(request, message=None, opening=None, closing=None):
        if opening:
            print('Just started')

        if closing:
            print('Connection closed.')

        if message:
            if message == 'close':
                request.finish()
            else:
                return message.upper() # Supports JSONable objects, like dict, list, tuple, etc.
    """

    def _wrapper(request, *args, **kwargs):
        # Opening...
        kwargs['opening'] = True
        kwargs['closing'] = False
        func(request, *args, **kwargs)

        def close():
            request._ws_closed = True
        request.close_websocket = close

        # Sending messages
        kwargs['opening'] = False
        while not getattr(request, '_ws_closed', False):
            try:
                message = request.ws.wait()
                ret = func(request, message, *args, **kwargs)
                if ret is None:
                    continue
                elif isinstance(ret, (tuple, list, dict)):
                    ret = simplejson.dumps(ret, cls=CustomJSONEncoder)
                request.ws.send(ret)
            except socket.error:
                break

        func(request, None, opening=False, closing=True)
    return _wrapper

def websocket_new(func):
    """
    Decorator for WebSocket views. Just declare a function like this:

    @websocket
    def my_websocket_handler(request, message=None, opening=None, closing=None):
        if opening:
            print('Just started')

        if closing:
            print('Connection closed.')

        if message:
            if message == 'close':
                request.close_websocket()
            else:
                return message.upper() # Supports JSONable objects, like dict, list, tuple, etc.
    """

    def _wrapper(request, *args, **kwargs):
        request.is_asynchronous = True

        # Bad request. TODO: This validation should be a little more mature to get better
        if not (request.META.get('HTTP_CONNECTION','').lower() == 'upgrade' and
                request.META.get('HTTP_UPGRADE','').lower() == 'websocket'):
            return HttpResponseBadRequest(headers={'Connection':'close'})

        # Choosing the protocol version
        protocol_version = request.META.get('HTTP_SEC_WEBSOCKET_VERSION', None)
        if protocol_version in ('8','7'):
            request.ws = WebSocketProtocol8(request, func, func_args=args, func_kwargs=kwargs)
        else:
            return HttpVersionNotSupported('WebSocket protocol version %s is not supported.'%protocol_version)

        # Start listening as a websocket handler
        request.ws.start()
    return _wrapper

class WebSocketProtocol(object):
    _closed = False

    def __init__(self, request, func, func_args=None, func_kwargs=None):
        self.request = request
        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs
        self._closed = False

        self.request.finish = self.finish
        self.request.send_message = self.send_message

    def start(self):
        # Opening...
        self.open()

        # Sending messages
        kwargs = {'opening': False, 'closing': False}
        kwargs.update(self.func_kwargs)
        while not self._closed:
            message = self.wait()
            self.func(self.request, message, *self.func_args, **kwargs)

        # Closing
        self.close()

    def open(self):
        kwargs = {'opening': True, 'closing': False}
        kwargs.update(self.func_kwargs)
        self.func(self.request, *self.func_args, **kwargs)

    def close(self):
        kwargs = {'opening': False, 'closing': True}
        kwargs.update(self.func_kwargs)
        self.func(self.request, *self.func_args, **kwargs)

    def wait(self):
        pass # TODO

    def finish(self):
        pass # TODO

    def send_message(self, data):
        # TODO
        if data is None:
            return

        elif isinstance(ret, (tuple, list, dict)):
            data = simplejson.dumps(data, cls=CustomJSONEncoder)

        self._write_frame(data)

class WebSocketProtocol8(WebSocketProtocol):
    pass

