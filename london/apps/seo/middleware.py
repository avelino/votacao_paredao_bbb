import app_settings
from london.http import Http404, HttpResponseRedirect, HttpResponse
from london.templates import render_to_string
from london.apps.seo.models import Rule

class SEOMiddleware(object):
    def process_exception(self, request, response, exception):
        if isinstance(exception, Http404):
            # Returns an empty favicon.ico file
            if request.path_info in ('/favicon.ico','/favicon.ico/') and app_settings.DEFAULT_EMPTY_FAVICON:
                return HttpResponse('', mime_type='image/icon')

            # Appends the slash to the end of the URL
            if not request.path_info.endswith('/') and app_settings.APPEND_SLASH:
                return HttpResponseRedirect(request.path_info + '/')

class RobotsMiddleware(object):
    def process_exception(self, request, response, exception):
        if request.path_info == '/robots.txt':
            rules = request.site['rules']
            return HttpResponse(render_to_string('seo/robots.txt', {'rules':rules}), mime_type='text/plain')

