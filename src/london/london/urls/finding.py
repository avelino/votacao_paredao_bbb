from london.conf import settings
from london.utils.imports import import_anything
from london.utils.regexp import replace_groups
from london.urls.parsing import resolve_url
from london.exceptions import NoReverseMatch

def reverse(name_or_view, args=None, kwargs=None, service='public'):
    """
    Returns the URL string for a given URL name, view name or view object and named and no-named
    arguments.
    
    This function cannot stay in the same module of parser and defining functions because it
    imports the project (could start a circular reference).
    """
    args = args or []
    kwargs = kwargs or {}

    if args and kwargs:
        raise ValueError("It's not possible to find a URL by *args and **kwargs both informed.")
    
    # Tries to import name_or_view if it's a valid object path
    if isinstance(name_or_view, basestring):
        try:
            name_or_view = import_anything(name_or_view)
        except ImportError:
            pass

    urls = settings.SERVICES[service]['urls']
    
    if isinstance(urls, basestring):
        urls = import_anything(urls)

    def strip_url(path):
        if path.startswith('^'): path = path[1:]
        if path.endswith('$'): path = path[:-1]
        return path

    def find_url(_name_or_view, _url_patterns, _args, _kwargs):
        for _url in _url_patterns:
            if isinstance(_url.children_urls, (tuple, list)):
                try:
                    path = find_url(_name_or_view, _url.children_urls, _args, _kwargs)
                except NoReverseMatch:
                    continue

                if path is not None:
                    return strip_url(_url.exp) + path
            elif _name_or_view in (_url.view, _url.name):
                return strip_url(_url.exp)

        raise NoReverseMatch('URL "%s" wasn\'t found with args %s and kwargs %s'%(
            name_or_view, args or '()', kwargs or '{}'))

    # Finds the URL for the requested arguments
    full_path = '/' + find_url(name_or_view, urls.url_patterns, args, kwargs)

    return replace_groups(full_path, args, kwargs)

