from london.urls.defining import patterns, include
from london.conf import settings
from london.apps.staticfiles.views import url_serve

from london.apps import ajax
ajax.site.root_url = '/ajax/'

from london.apps import admin
admin.site.root_url = '/admin/'
admin.site.load_from_applications()
admin.site.ajax_site = ajax.site

if settings.LOCAL:
    url_patterns = patterns('', url_serve(settings.STATIC_URL[1:], settings.STATIC_ROOT))

url_patterns += patterns('public.views',
    (r'^$', 'home', {}, 'home'),
    (r'^simple/$', 'simple_page', {}, 'simple_page'),
    (r'^notifications/$', 'notifications', {}, 'notifications'),
    (r'^string/$', 'just_string', {}, 'just_string'),
    (r'^websockets/$', 'websockets', {}, 'websockets'),
    (r'^ws1/$', 'ws_handler', {}, 'ws_handler'),
    (r'^my-documents/', include('my_documents.urls')),
    (r'^themes/', include('london.apps.themes.urls')),
    (r'^sse/$', 'sse', {}, 'sse'),
    (r'^sse-handler/$', 'sse_handler', {}, 'sse_handler'),
    (r'^memory/$', 'memory', {}, 'memory'),
    (r'^force-error/$', 'force_error', {}, 'force_error'),
    (r'^ajax/', include(ajax.site.urls)),
    (r'^admin/', include(admin.site.urls)),
    )

