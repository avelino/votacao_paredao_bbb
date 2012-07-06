import os

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

from london.http import HttpResponse, HttpRequest
from london.conf import settings
from london.exceptions import TemplateNotFound
from london.templates.signals import template_global_context, get_template_loaders
from london.utils.imports import import_anything
from london.core import load_apps

from jinja2 import Template, Environment, FileSystemLoader, ChoiceLoader
from jinja2.exceptions import TemplateNotFound as JinjaTemplateNotFound

INVALID_CONTEXT_VARS = ('self',)

def get_template_env(theme=None):
    """
    Creates and return the templates environment for multiple sources.
    """
    # Initializes the current environment
    custom_loaders = []
    if settings.TEMPLATE_LOADERS:
        def import_and_get_loader(s):
            try:
                path, loader_name = s.rsplit('.', 1)
            except ValueError:
                raise ImproperlyConfigured("Invalid TEMPLATE_LOADER '%s'."%s)

            try:
                mod = import_anything(path)
            except ImportError:
                raise ImproperlyConfigured("Module '%s' wasn't found."%path)

            try:
                loader = getattr(mod, loader_name)
            except AttributeError:
                raise ImproperlyConfigured("Loader '%s' not found."%loader_name)
            
            return loader()
        custom_loaders = [ import_and_get_loader(loader) for loader in settings.TEMPLATE_LOADERS ]
    loaders = reduce(lambda a,b: a+b, get_template_loaders.send())
    loader = ChoiceLoader(custom_loaders + loaders)
    template_env = Environment(loader=loader, extensions=settings.TEMPLATE_EXTENSIONS)
    template_env.theme = theme

    # Loads template filters
    for path in settings.TEMPLATE_FILTERS:
        mod = import_anything(path)

        for attr in dir(mod):
            item = getattr(mod, attr)
            if getattr(item, 'environmentfilter', False):
                template_env.filters[attr] = item

    return template_env

def template_dirs_from_settings(**kwargs):
    return [FileSystemLoader(directory) for directory in settings.TEMPLATE_DIRS]
get_template_loaders.connect(template_dirs_from_settings)

def template_dirs_from_apps(**kwargs):
    def template_dir(app_mod):
        return os.path.join(app_mod.__path__[0], 'templates')
    return [FileSystemLoader(template_dir(app)) for app in load_apps()]
get_template_loaders.connect(template_dirs_from_apps)

def get_context(request, base_dict=None):
    ret = {}

    # Invalid context type
    if base_dict and not isinstance(base_dict, dict):
        raise TypeError('Invalid context of type %s: %s' % (type(base_dict), base_dict))

    ret.update(base_dict or {})

    if request:
        for t_context in template_global_context.send(request=request):
            ret.update(t_context)

    # Remove invalid context variables
    for name in INVALID_CONTEXT_VARS:
        ret.pop(name, None)
    return ret

def ensure_redirect(content, path_info):
    # This code ensures the code will reload as a direct URL instead of Ajax in a history
    # getting back from an outside page
    if not content.strip().startswith('<!doctype html>') and '<base ' in content:
        content = '<script>window.location = \'%s\';</script>'%path_info + content
    return content

def render_base(content, context, theme=None):
    """Put the content inside it's base template to return as once"""

    # FIXME This code using BeautifulSoup isn't good. The right way should be using Jinja's low level API for that.
    soup = BeautifulSoup(content)
    base_tag = soup.findAll('base')

    if base_tag:
        base_content = render_to_string(dict(base_tag[0].attrs)['template_name'], context, theme=theme)
        base_soup = BeautifulSoup(base_content)

        # Replaces the containers' content with piece's content
        for piece in soup.findAll('piece'):
            name = dict(piece.attrs)['name']
            containers = base_soup.findAll(attrs={'container':name}) +\
                         base_soup.findAll(attrs={'mirroring':name})
            for container in containers:
                if container.attrMap.get('container_param', None):
                    container[container.attrMap['container_param']] = piece.text
                else:
                    container.clear() # Clears children before to set new content (i.e. replacement)
                    for item in piece.contents:
                        if unicode(item).strip():
                            container.append(item)

        content = unicode(base_soup)

    # FIXME - this lines shouldn't exist
    content = content.replace('<!<!', '<!').replace('>>','>')
    content = content.replace('<!--<!--','<!--').replace('-->-->','-->')

    return content

def render_to_response(request, template_path, context=None, ajax_base=True, http_class=HttpResponse,
        http_kwargs=None):
    context = get_context(request, context or {})
    http_kwargs = http_kwargs or {}

    content = render_to_string(template_path, context, theme=getattr(request,'theme',None), is_ajax=request.is_ajax(),
                http_kwargs=http_kwargs)

    if request.is_ajax():
        content = ensure_redirect(content, request.path_info)
    
    return http_class(content, **http_kwargs)

def render_template(template_path, http_class=HttpResponse, **deckw):
    """
    This is a decorator that uses a view function returning a dictionary to render by Jinja template.

    View functions under this decorator can return a dictionary dictionary and values or a tuple with
    the template path and the context dictionary.
    """
    def _inner(func):
        def _view(*args, **kwargs):
            try:
                request = kwargs['request']
            except KeyError:
                if isinstance(args[0], HttpRequest):
                    request = args[0]
                elif isinstance(args[1], HttpRequest):
                    request = args[1]

            context = func(*args, **kwargs)

            if isinstance(context, HttpResponse):
                return context

            context = get_context(request, context)

            # Loads the template from a list, considering kwargs to compose the template path
            content = render_to_string(template_path, context, theme=getattr(request,'theme',None), is_ajax=request.is_ajax(),
                        http_kwargs=kwargs)
            if request.is_ajax():
                content = ensure_redirect(content, request.path_info)

            return http_class(content, **deckw)
        return _view
    return _inner

def render_to_string(template_path, context=None, theme=None, is_ajax=False, http_kwargs=None):
    # Loads the template from a list, considering kwargs to compose the template path
    tpl = None
    env = get_template_env(theme=theme)
    http_kwargs = http_kwargs or {}
    template_paths = template_path if isinstance(template_path, (tuple,list)) else [template_path]
    for path in template_paths:
        try:
            tpl = env.get_template(path%http_kwargs)
            break
        except (JinjaTemplateNotFound, TemplateNotFound):
            continue
    if not tpl:
        raise TemplateNotFound('Template(s) %s not found'%', '.join(template_paths))

    context = context or {}
    content = tpl.render(**context).strip()

    if not is_ajax:
        content = render_base(content, context, theme=theme)

    return content.strip()

def render_content(content, context=None, request=None):
    """Renders a template content and returns it as a string."""
    env = get_template_env()
    tpl = env.from_string(content) #Template(content)
    context = get_context(request, context or {})
    return tpl.render(**context).strip()

def get_global_contexts(request, **kwargs):
    """
    Function responsible for find all template context processors from settings and return them to
    the global template context.
    """
    context = {}

    for path in settings.TEMPLATE_CONTEXT_PROCESSORS:
        func = import_anything(path)
        context.update(func(request))

    return context
template_global_context.connect(get_global_contexts)

