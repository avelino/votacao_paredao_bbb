#from london.templates import render_template
from london.http import HttpResponse

try:
    from guppy import hpy as guppy_hpy
except ImportError:
    guppy_hpy = None

#@render_template('home')
def home(request):
    #return locals()
    return HttpResponse('This is a very simple project.')

def memory(request):
    heap = guppy_hpy().heap() if guppy_hpy else ''
    return HttpResponse(unicode(heap), mime_type='text/plain')

def force_error(request):
    raise Exception('Testing exception management.')

