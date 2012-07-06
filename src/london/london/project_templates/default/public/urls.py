from london.urls.defining import patterns, include
from london.conf import settings
from london.apps.staticfiles.views import url_serve

#from london.apps import ajax
#ajax.site.root_url = '/ajax/'

#from london.apps import admin
#admin.site.root_url = '/admin/'
#admin.site.load_from_applications()
#admin.site.ajax_site = ajax.site

url_patterns = patterns('public.views',
        (r'^$', 'home', {}, 'home'),
)

if settings.LOCAL:
    url_patterns += patterns('', url_serve(settings.STATIC_URL[1:], settings.STATIC_ROOT))

