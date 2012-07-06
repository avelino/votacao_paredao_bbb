"""
Server-Sent Events is a stable and simpler alternative to WebSockets and Long Polling.
"""
import time
import socket
try:
    import json as simplejson
except ImportError:
    import simplejson

from london.utils.json_encoding import CustomJSONEncoder
from london.exceptions import ConnectionClosed

def server_sent_event_source(*args, **kwargs):
    """
    Decorator for Server-Sent Events views.
    More about this protocol in http://dev.w3.org/html5/eventsource/

    Can be used just as a simple decorator, like this:

        from london.sse import server_sent_event_source
        from london.exceptions import ConnectionClosed

        @server_sent_event_source
        def my_view(request, is_opening=None):
            try:
                request.send_event('message', 'data')
                request.run_again_after(10)
            except ConnectionClosed:
                request.finish()

    or can be used setting parameters, like this

        @server_sent_event_source(retry=None)
        def my_view(request, is_opening=None):
            request.send_event('message', 'data')
    """
    retry = kwargs.get('retry', 30000)
    headers = kwargs.get('headers', {})

    def _inner(func):
        def _wrapper(request):
            request.sse_first_time = True
            request.is_asynchronous = True

            # Basic necessary HTTP headers
            request.write('HTTP/1.1 200 OK\n')
            headers.setdefault('Content-Type','text/event-stream; charset=utf-8') # ; charset=utf-8
            headers.setdefault('Cache-Control','no-cache')
            headers.setdefault('Connection','keep-alive')

            try:
                # Write headers in the stream
                for k,v in headers.items():
                    request.write('%s: %s\n'%(k,v))

                # Sets the retry time
                if retry:
                    request.write('retry: %s\n'%retry)
            except ConnectionClosed:
                pass

            def send(id, msg):
                """Function to send a new message to the event client"""
                msg = simplejson.dumps(msg, cls=CustomJSONEncoder)
                try:
                    request.write('id: %s\ndata: %s\n\n'%(id, msg))
                except socket.error:
                    request.finish()
                finally:
                    pass
            request.send_event = send

            def run_again_after(seconds):
                # Adds a timeout for running
                request._run_again_after_seconds = seconds
            request.run_again_after = run_again_after

            func(request, request.sse_first_time)
            request.sse_first_time = False

            if getattr(request, '_run_again_after_seconds', None):
                def run_again():
                    func(request, request.sse_first_time)
                    request.run_with_timeout(request._run_again_after_seconds, run_again)
                run_again()
        return _wrapper

    if args and callable(args[0]):
        return _inner(args[0])
    else:
        return _inner

