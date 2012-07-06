from london.apps.sites import app_settings
from london.utils.imports import import_anything
from london.apps.sites.models import SiteMirror, Site
from london.http import HttpResponsePermanentRedirect

class SiteDetectMiddleware(object):
    def process_request(self, request):
        request.site = None

        # Try using site detecting function
        if app_settings.DETECTING_FUNCTION:
            try:
                func = import_anything(app_settings.DETECTING_FUNCTION)
                site_or_mirror = func(request)

                if isinstance(site_or_mirror, SiteMirror):
                    request.site = site_or_mirror['site']
                    if app_settings.MIRROR_PERMANENT_REDIRECT:
                        scheme = 'https' if (request.is_secure() or site_or_mirror['https_is_default']) else 'http'
                        new_hostname = site_or_mirror['site']['hostname']
                        if request.META.get('SERVER_PORT', 80) != 80:
                            new_hostname += ':%s'%request.META['SERVER_PORT']
                        return HttpResponsePermanentRedirect('%s://%s/'%(scheme, new_hostname))
                else:
                    request.site = site_or_mirror
            except ImportError:
                pass

        # Treats the inactive site
        if ((not request.site or not request.site['is_active']) and
            not app_settings.ACCEPT_INACTIVE_SITE and
            app_settings.INACTIVE_SITE_VIEW):
            view = import_anything(INACTIVE_SITE_VIEW)
            return view(request)

        # Creates a new site if there is no site existing
        if Site.query().count() == 0 and app_settings.CREATE_SITE_IF_EMPTY:
            request.site = Site(_save=True, name='localhost', hostname='localhost', default=True, active=True)

