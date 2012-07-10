import re

from london.http import Http404, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse
from london.apps.redirects.models import Redirect

class RedirectMiddleware(object):
    _exps = {} # This is a class variable, keep it with {} here

    def process_request(self, request):
        if not getattr(request, 'site', None):
            return

        for redirect in request.site['redirects'].order_by('url_pattern'):
            if not self._exps.get(redirect['url_pattern'], None):
                self._exps[redirect['url_pattern']] = re.compile('^'+redirect['url_pattern']+'$')

            exp = self._exps[redirect['url_pattern']]
            m = exp.match(request.path_info)

            if m:
                if m.groups():
                    url = redirect['url_destination']
                    url = url.replace('$0', request.path_info)
                    for num, group in enumerate(m.groups()):
                        url = url.replace('$%s'%(num+1), group)
                else:
                    url = redirect['url_destination']

                resp_class = HttpResponsePermanentRedirect if redirect['is_permanent'] else HttpResponseRedirect
                return resp_class(url)

