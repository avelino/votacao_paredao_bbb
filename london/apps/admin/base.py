import os

from london.templates import render_template
from london.urls import patterns, include, reverse
from london.apps.admin.app_settings import CURRENT_SITE_FILTER
from london.utils.imports import import_anything
from london.utils.slugs import slugify
from london.utils.strings import make_title
from london.apps.auth.authentication import login_required, permission_required, user_logout
from london.apps.admin.forms import AuthForm, ChangePasswordForm
from london.http import HttpResponseRedirect, JsonResponse
from london.apps.ajax.tags import redirect_to
from london.apps.sites.models import Site
from london.core import load_apps
from london.apps.admin import signals

class ApplicationAlreadyRegistered(Exception): pass
class InvalidApplicationName(Exception): pass

class AdminSite(object):
    """
    Represents an administration site, containing a couple of applications and their modules.
    """
    applications = None
    _ajax_site = None

    def __init__(self, root_url=None):
        self.root_url = root_url
        self.applications = {}

    def get_ajax_site(self):
        return self._ajax_site
    def set_ajax_site(self, site):
        self._ajax_site = site

        scripts_dir = getattr(self, 'scripts_dir', None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
        self._ajax_site.register_scripts_dir('admin', scripts_dir)

        styles_dir = getattr(self, 'styles_dir', None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles')
        self._ajax_site.register_styles_dir('admin', styles_dir)
    ajax_site = property(get_ajax_site, set_ajax_site)

    def get_login_url(self):
        return '%slogin/'%self.root_url

    def login_req(self, view_func):
        return login_required(url=self.get_login_url())(view_func)

    def get_module_base_url(self, request):
        plain_url = request.path_info[len(self.root_url):]
        bits = filter(bool, plain_url.split('/'))
        return '%s%s/%s/'%(self.root_url, bits[0], bits[1])

    def get_module_add_url(self, request):
        return '%sadd/'%self.get_module_base_url(request)

    def get_module_serialize_url(self, request):
        return '%sserialize/'%self.get_module_base_url(request)

    def get_module_edit_url(self, request, obj):
        return '%s%s/'%(self.get_module_base_url(request), obj['pk'])

    def get_module_delete_url(self, request, obj):
        return '%s%s/delete/'%(self.get_module_base_url(request), obj['pk'])

    def get_after_logout_url(self):
        return self.root_url

    def set_site(self, request, pk, **kwargs):
        """Select the current site to filter in Admin for this session."""
        del request.session[CURRENT_SITE_FILTER]

        # If no site exists for the given PK, let it empty
        if pk == '-unselect-':
            request.session[CURRENT_SITE_FILTER] = ''
        elif Site.query().filter(pk=pk).count() > 0:
            request.session[CURRENT_SITE_FILTER] = pk

        return JsonResponse('{"status":"ok", "redirect":"%s"}' % request.GET['goto'] if 'goto' in request.GET else '')

    @property
    def urls(self):
        ret = patterns('',
                (r'^$', self.login_req(self.home_view), {}, 'admin_home'),
                (r'^login/$', self.login_form, {}, 'admin_login'),
                (r'^logout/$', self.logout_view, {}, 'admin_logout'),
                (r'^change-password/$', self.change_password_form, {}, 'admin_change_password'),
                (r'^set/site/(?P<pk>[\w-]+)/$', self.set_site, {}, 'admin_set_site'),
                (r'^stats/$', self.login_req(self.stats_view), {}, 'admin_stats'),
                )

        for app in self.get_applications():
            ret.extend(patterns('',
                (r'^(?P<app>%s)/'%app.name.lower(), include(app.get_urls())),
                ))

        return ret

    def load_from_applications(self, *apps):
        """
        Loads applications given as arguments or all of installed applications if empty.
        """
        apps = apps or load_apps()
        for mod in apps:
            try:
                admin_mod = import_anything('admin', mod)
            except ImportError as e:
                continue

            for attr in dir(admin_mod):
                cls = getattr(admin_mod, attr)
                if isinstance(cls, type) and issubclass(cls, AdminApplication):
                    self.register_application(getattr(admin_mod, attr))

    def register_application(self, app_class):
        # Gets the name or the module name
        if app_class.name:
            name = app_class.name
        else:
            name = app_class.__module__.split('.')[-2]
            app_class.name = name

        # Validates application already registered
        if self.applications.get(name, app_class) != app_class:
            raise ApplicationAlreadyRegistered('There is already another application registered with the name '+name)
        elif slugify(name) != name:
            raise InvalidApplicationName('The name "%s" should be "%s" to be valid'%(name, slugify(name)))

        self.applications[name] = app_class

    def get_applications(self, request=None):
        apps = [cls(self, request) for name, cls in self.applications.items()]
        apps.sort(lambda a,b: cmp(a.get_title(), b.get_title()))

        return apps

    def get_sites(self):
        return [{'pk':unicode(site['pk']), 'name':site['name']} for site in Site.query()]

    @render_template('admin/home.html')
    def home_view(self, request):
        return {'applications': self.get_applications(request)}

    @render_template('admin/stats.html')
    def stats_view(self, request):
        boxes = signals.collect_stats.send(admin_site=self, request=request)
        if boxes:
            boxes = reduce(lambda a,b:a+b, boxes)
            boxes.sort(lambda a,b: cmp(a.get('order',0), b.get('order',0)) or cmp(a.get('title',0), b.get('title',0)))
        return {'boxes':boxes}

    @property
    def login_form(self):
#        AuthForm._meta.fields['next'].initial =  request.GET.get('next', None) or self.root_url
        return AuthForm

    @property
    def change_password_form(self):
        ChangePasswordForm._meta.fields['next'].initial = self.root_url
        return ChangePasswordForm

    def logout_view(self, request):
        user_logout(request)
        return redirect_to(request, self.get_after_logout_url())


class AdminApplication(object):
    """
    Represents a set of modules in an admin site.
    """
    name = None
    title = None
    modules = None
    site = None
    request = None

    def __init__(self, site=None, request=None):
        self.site = site
        self.request = request

    def get_title(self):
        return self.title or make_title(self.name)

    @property
    def url(self):
        return '%s%s/'%(self.site.root_url, self.name)

    def get_modules(self):
        return [cls(self.site, self, self.request) for cls in self.modules]

    def get_urls(self):
        ret = patterns('',
                (r'^$', self.site.login_req(self.home_view), {}, 'admin_%s_home'%self.name.lower()),
                )

        for module in self.get_modules():
            ret.extend(patterns('',
                (r'^(?P<module>%s)/'%module.name.lower(), include(module.get_urls())),
                ))

        return ret

    @render_template(('admin/%(app)s/home.html', 'admin/app_home.html'))
    def home_view(self, request, **kwargs):
        return {
                'modules': self.get_modules(),
                }

