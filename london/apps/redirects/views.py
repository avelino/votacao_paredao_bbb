from london.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from london.urls import reverse
from london.exceptions import NoReverseMatch

def redirect_to(request, url, permanent=False):
    """
    Generic view for redirection. The argument "url" supports a url name, a view path or a usual URL.
    """
    try:
        url = reverse(url)
    except (NoReverseMatch, SyntaxError):
        pass

    if permanent:
        return HttpResponsePermanentRedirect(url)
    else:
        return HttpResponseRedirect(url)

