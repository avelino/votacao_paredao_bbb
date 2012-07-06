import os
import time
import datetime
import simplejson

from london.templates import render_template
from london.http import HttpResponse
from london.sse import server_sent_event_source
from london.websockets import websocket_new as websocket
from london.exceptions import ConnectionClosed

try:
    from guppy import hpy as guppy_hpy
except ImportError:
    guppy_hpy = None

@render_template('home')
def home(request):
    return locals()

@render_template('notifications.html')
def notifications(request):
    request.info('Testing info.')
    request.error('Testing error.')
    request.warning('Testing warning.')
    request.debug('Testing debug.')
    return locals()

@render_template('simple_page.html')
def simple_page(request):
    return locals()

def just_string(request):
    return 'this is just a string returning as status 200'

@render_template('websockets.html')
def websockets(request):
    return locals()

@render_template('sse.html')
def sse(request):
    return locals()

@server_sent_event_source
def sse_handler(request, first_time=None):
    if first_time or not hasattr(request, 'counter'):
        request.counter = 0

    if request.counter > 50:
        request.finish()
    else:
        try:
            request.send_event('message', request.counter)
        except ConnectionClosed:
            return

        request.counter += 1

    request.run_again_after(3)
    print '5 seconds...'

@websocket
def ws_handler(request, message=None, opening=False, closing=False):
    print opening, closing
    if not opening and not closing:
        print (message,)
        if message.lower().strip() == 'close':
            request.finish()
        else:
            request.send_message(message.upper())

def memory(request):
    heap = guppy_hpy().heap() if guppy_hpy else ''
    return HttpResponse(unicode(heap), mime_type='text/plain')

def force_error(request):
    raise Exception('Testing exception management.')

