import os

from london.templates import render_template
from london.urls import patterns, include
from london.conf import settings
from london.utils.imports import import_anything
from london.utils.slugs import slugify
from london.utils.strings import make_title
from london.http import HttpResponseRedirect, HttpResponseForbidden
from london.apps.rest.modules import BaseModule
from london.core import load_apps
from london.apps.rest.models import ExternalApplication
from london.apps.rest import app_settings

class ApplicationAlreadyRegistered(Exception): pass
class InvalidApplicationName(Exception): pass

class RestSite(object):
    modules = None
    root_prefix = ''
    title = None

    def __init__(self, root_url=None, title=None):
        self.root_url = root_url
        self.modules = {}
        self.title = title or self.title

    def __unicode__(self):
        return self.title

    @property
    def urls(self):
        ret = patterns('',
                (r'^$', self.auth_required(self.root_view), {}, '%s_root'%self.root_prefix),
                )

        for module in self.get_modules():
            ret.extend(patterns('', (r'^(?P<module>%s)/'%module.name, include(module.get_urls()))))

        return ret

    def auth_required(self, func):
        def _inner(request, *args, **kwargs):
            if not self.clean_authentication(request):
                return HttpResponseForbidden('Need authentication.')
            return func(request, *args, **kwargs)
        return _inner

    def clean_authentication(self, request):
        if not app_settings.EXTERNAL_APPLICATION_AUTH:
            return True

        try:
            consumer_key = request.COOKIES.get('consumer_key',None).value
        except AttributeError:
            return False

        try:
            request.external_application = ExternalApplication.query().get(consumer_key=consumer_key)
            return consumer_key and request.external_application['consumer_key'] == consumer_key
        except ExternalApplication.DoesNotExist:
            return False

    @render_template('rest/index.html')
    def root_view(self, request):
        return {'modules': self.get_modules(request)}

    def load_from_applications(self, *apps):
        """
        Loads applications given as arguments or all of installed applications if empty.
        """
        apps = apps or load_apps()
        for mod in apps:
            try:
                rest_mod = import_anything('rest', mod)
            except ImportError as e:
                continue

            for attr in dir(rest_mod):
                cls = getattr(rest_mod, attr)
                if isinstance(cls, type) and issubclass(cls, BaseModule):
                    self.register_module(getattr(rest_mod, attr))

    def register_module(self, module_class):
        # Gets the name or the module name
        if not module_class.name:
            module_class.name = module_class.model.__name__.lower()
        name = module_class.name

        # Validates modules already registered
        if self.modules.get(name, module_class) != module_class:
            raise ApplicationAlreadyRegistered('There is already another module registered with the name '+name)
        elif slugify(name) != name:
            raise InvalidApplicationName('The name "%s" should be "%s" to be valid'%(name, slugify(name)))

        self.modules[name] = module_class

    def get_modules(self, request=None):
        apps = [cls(self, request) for name, cls in self.modules.items()]
        apps.sort(lambda a,b: cmp(a.get_title(), b.get_title()))

        return apps

