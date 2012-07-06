from gevent.pywsgi import WSGIServer
import gevent
from gevent import monkey; monkey.patch_all()

def hello_world(env, start_response):
    gevent.sleep(5)
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["<b>hello world</b>"]

print 'Serving on 8088...'
WSGIServer(('127.0.0.1', 8888), hello_world).start()
