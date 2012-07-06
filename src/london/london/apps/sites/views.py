from london.http import Http404
from london.utils.translation import ugettext as _

def inactive_site(request):
    raise Http404(_('Site is inactive. Sorry for this inconvenience and come back soon.'))

