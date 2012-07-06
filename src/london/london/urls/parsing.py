import re

from london.utils.imports import import_anything
from london.exceptions import URLNotFound

class URLPattern(object):
    def __init__(self, exp, path, params=None, name=None):
        self.exp = exp
        self.regexp = re.compile(self.exp)
        self.path = path
        self.params = params
        self.name = name

        self.parse_view()

    def __repr__(self):
        return '<URLPattern %s %s %s %s>'%(self.exp, self.path, self.params, self.name)

    def parse_view(self):
        self.children_urls = None
        self.view = None

        if isinstance(self.path[1], (tuple, list)):
            self.children_urls = self.path[1]
        elif callable(self.path[1]):
            self.view = self.path[1]
        elif not isinstance(self.path[0], basestring) and isinstance(self.path[1], basestring):
            self.view = getattr(self.path[0], self.path[1])
        else:
            self.view = import_anything(self.path)

    def match(self, path_info):
        return self.regexp.match(path_info)

    def resolve(self, path_info):
        m = self.match(path_info)
        ret, u_args, u_kwargs = self, (), {}

        # If doesn't match, just returns None
        if not m:
            return None, (), {}

        # If has children urls (probably from an include), gets from children
        if self.children_urls:
            ret, u_args, u_kwargs = resolve_url(self.regexp.sub('', path_info), self.children_urls)

        # Merges the arguments
        if ret:
            if m.groupdict():
                args = u_args
                kwargs = m.groupdict()
                kwargs.update(u_kwargs)
            else:
                args = m.groups() + u_args
                kwargs = u_kwargs

        return ret, args, kwargs

def resolve_url(path_info, urls):
    """
    Finds the right URL from a list of URLs for a given path_info
    """
    if isinstance(urls, (tuple, list)):
        url_patterns = urls
    else:
        if isinstance(urls, basestring):
            urls = import_anything(urls)
        url_patterns = urls.url_patterns

    for url in url_patterns:
        ret_url, args, kwargs = url.resolve(path_info)

        if ret_url:
            return ret_url, args, kwargs

    raise URLNotFound('URL for "%s" doesn\'t exist.'%path_info)

class LazyURLParam(object):
    """Class for lazy parameter retrieving for URL parameters."""

    def __init__(self, func):
        self.func = func

    def __call__(self, request, *args, **kwargs):
        return self.func(request, *args, **kwargs)

def resolve_lazy_params(request, args, kwargs):
    args = args or []
    kwargs = kwargs or {}
    return (
            tuple([(arg(request) if isinstance(arg, LazyURLParam) else arg) for arg in args]),
            dict([(key,(arg(request) if isinstance(arg, LazyURLParam) else arg)) for key,arg in kwargs.items()]),
            )

