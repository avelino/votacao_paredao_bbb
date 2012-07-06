from london.utils.imports import import_anything
from london.urls.parsing import URLPattern

def patterns(module, *urls):
    """
    Makes a treatment on given module and urls to make them the best possible for URL parser.
    """
    new_urls = []

    for url in urls:
        params = url[2] if len(url) > 2 else {}
        name = url[3] if len(url) > 3 else None

        new_urls.append(URLPattern(url[0], (module, url[1]), params, name))

    return new_urls

def include(module):
    """
    Includes a module object or a module path containing another url_patterns to parse a group of URLs.
    """
    module = import_anything(module) if isinstance(module, basestring) else module

    if isinstance(module, (list,tuple)):
        return module
    else:
        return module.url_patterns

