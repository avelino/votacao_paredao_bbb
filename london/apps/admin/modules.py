from london.urls import patterns, reverse
from london.apps.admin.app_settings import CURRENT_SITE_FILTER
from london.templates import render_template, render_to_string
from london.forms.models import modelform_factory, ModelFormMetaclass, BaseModelForm
from london.http import HttpResponseRedirect, Http404, HttpResponse
from london.utils.strings import make_title
from london.apps.ajax.tags import redirect_to
from london.apps.auth.authentication import permission_required
from london.apps.serialization.core import serialize, get_serializer
from london.apps.sites.models import Site
from london.utils.slugs import slugify
from london.db import models
from london.apps.admin import signals


class BaseModuleForm(BaseModelForm):
    __metaclass__ = ModelFormMetaclass

    def __del__(self):
        self.admin_module._form_class = None

    def _ajax_post(self, *args, **kwargs):
        resp = super(BaseModuleForm, self)._ajax_post(*args, **kwargs)

        if self.saved:
            resp = redirect_to(self.request, self.request.path_info + '../')

        return resp

    def get_site_field(self):
        """Returns True if the model class has a ForeignKey to Site model class."""
        for name, field in self._meta.model._meta.fields.items():
            if isinstance(field, models.ForeignKey) and field.related == Site._meta.path_label:
                return field

    def get_initial(self, initial=None):
        initial = initial or super(BaseModuleForm, self).get_initial(initial)

        # Detects a ForeignKey field related to Site model class
        site_field = self.get_site_field()
        if site_field and self.request.session.get(CURRENT_SITE_FILTER, None):
            site_field.initial = self.request.session[CURRENT_SITE_FILTER]
            initial['site'] = site_field.initial

        return initial

    def default_context(self, *args, **kwargs):
        context = {}
        context['object_verbose_name'] = self._meta.model._meta.verbose_name
        context['object_verbose_name_plural'] = self._meta.model._meta.verbose_name_plural

        additional_buttons = signals.module_form_buttons.send(module=self.admin_module, form=self)
        context['additional_buttons'] = ''.join(filter(bool, additional_buttons))

        additional_links = signals.module_form_links.send(module=self.admin_module, form=self)
        context['additional_links'] = ''.join(filter(bool, additional_links))

        return context

    def save(self, commit=True, force_new=False):
        obj = super(BaseModuleForm, self).save(commit=commit, force_new=bool(self.request.POST.get('save_as_new', None)))
#        site_field = self.get_site_field()
#        if site_field and self.request.session.get(CURRENT_SITE_FILTER, None):
#            try:
#                obj[site_field.name] = Site.query().get(pk = self.request.session[CURRENT_SITE_FILTER])
#                obj.save()
#            except Site.DoesNotExist:
#                pass
        return obj

class BaseModule(object):
    name = None
    title = None

    def __init__(self, site=None, application=None, request=None):
        self.site = site
        self.application = application
        self.request = request

    def get_title(self):
        return self.title or make_title(self.name)

    @property
    def url(self):
        return '%s%s/'%(self.application.url, self.name.lower())

    def get_urls(self):
        return patterns('',
                (r'^$', self.site.login_req(self.home_view), {}, 'admin_%s_%s_home'%(self.application.name, self.name.lower())),
                )

    @render_template(('admin/%(app)s/%(module)s/home.html', 'admin/%(app)s/module_home.html', 'admin/module_home.html'))
    def home_view(self, request, **kwargs):
        return {}


class CrudModule(BaseModule):
    model = None
    list_display = None
    list_display_links = None
    list_layout = "fields"
    form = BaseModuleForm   # Used for used to set their customized form class
    _form_class = None      # Stores the internal copy of form class, specifically for this module
    fields = None
    fieldsets = None
    exclude = None
    readonly_fields = None
    list_per_page = 20
    search_fields = None

    def __init__(self, site=None, application=None, request=None):
        super(CrudModule, self).__init__(site, application, request)
        self.name = self.name or self.model.__name__
        self.title = self.model._meta.verbose_name_plural or make_title(self.name)

    def get_urls(self):
        return patterns('',
            (r'^$', self.site.login_req(self.list_view), {}, 'admin_%s_%s_list'%(self.application.name, self.name.lower())),
            (r'^add/$', self.site.login_req(self.form_class), {}, 'admin_%s_%s_add'%(self.application.name, self.name.lower())),
            (r'^serialize/$', self.site.login_req(self.serialize_view), {}, 'admin_%s_%s_serialize'%(self.application.name, self.name.lower())),
            (r'^(?P<pk>\w+)/$', self.site.login_req(self.form_class), {}, 'admin_%s_%s_edit'%(self.application.name, self.name.lower())),
            (r'^(?P<pk>\w+)/delete/$', self.site.login_req(self.delete_view), {}, 'admin_%s_%s_delete'%(self.application.name, self.name.lower())),
            )

    @render_template(('admin/%(app)s/%(module)s/list.html', 'admin/%(app)s/module_list.html', 'admin/module_list.html'))
    def list_view(self, request, **kwargs):
        sorted = {}
        if request.GET.get('sortby', None):
            sorted = {'by':request.GET.pop('sortby')[0], 'order': request.GET.pop('order')[0]}
        columns = self.get_columns(request, sorted)
        list_display_links = self.list_display_links or (columns[0]['name'],)

        def prepare_cell(obj, col):
            display = obj[col['name']] if obj[col['name']] is not None else ''
            ret = {'column':col, 'value':obj[col['name']], 'display':display}
            if col['name'] in list_display_links:
                ret['link'] = self.site.get_module_edit_url(request, obj) # TODO: Change pk for a way to set which field to use as natural key
            return ret

        def prepare_object(obj):
            obj.cells = [prepare_cell(obj, col) for col in columns]
            return obj
        
        def sort_objects(queryset):
            if 'by' in sorted:
                queryset = queryset.order_by(('-' if sorted['order'] == "desc" else '') + sorted['by'])
            return queryset

        def filter_objects(queryset):
            # filter by current selected site
            try:
                if 'site' in queryset.model._meta.fields and request.session[CURRENT_SITE_FILTER] != '':
                    site = Site.query().get(pk = request.session[CURRENT_SITE_FILTER])
                    queryset = queryset.filter(site=site)
            except:
                pass
            
            if request.GET:
                params = [(key, str(val)) for key, val in request.GET.items() if key not in ('q',) and not key.startswith('_')]
                queryset = queryset.filter(**dict(params))
            search_terms = request.GET.get('q', None)
            if self.search_fields is not None and search_terms:
                lookups = ["%s__icontains" % field for field in self.search_fields]
                search_filters = []
                bits = search_terms.split()
                for bit in bits:
                    queryset = queryset.filter_if_any(*[{lookup: bit} for lookup in lookups])
            return queryset

        objects = filter_objects(sort_objects(self.get_queryset(request))) # do sort before filtering to avoid passing sorting params to filtering

        list_block_template = "admin/block_list_%s_display.html" % self.list_layout
        return {
            'objects': objects,
            'columns': columns,
            'sorted': sorted,
            'object_verbose_name': self.model._meta.verbose_name,
            'object_verbose_name_plural': self.model._meta.verbose_name_plural,
            'list_block_template': list_block_template,
            'search_enabled': self.search_fields is not None,
            'search_block': self.get_search_block(request, columns, http_kwargs=kwargs),
            'module': self,
            'prepare_object': prepare_object,
            }

    def get_search_block(self, request, columns=None, http_kwargs=None):
        templates = ('admin/%(app)s/%(module)s/block_search.html', 'admin/%(app)s/block_search.html', 'admin/block_search.html')
        return render_to_string(
                templates,
                context={
                    'request':request,
                    'module':self,
                    'search_enabled': self.search_fields is not None,
                    'columns': columns,
                    'object_verbose_name': self.model._meta.verbose_name,
                    'search_url': self.url,
                    },
                is_ajax=request.is_ajax(),
                theme=getattr(request, 'theme', None),
                http_kwargs=http_kwargs,
                )

    def serialize_view(self, request, **kwargs):
        """FIXME: This function must be moved from here to the application "serialization" as part of a signal to customize admin
        without to make coupling (which is doing by this old way)."""
        objects = self.get_queryset(request)
        data = serialize(objects)
        serializer = get_serializer()
        file_name = '%s.%s'%(slugify(self.get_title()), serializer.extension)
        return HttpResponse(data, mime_type='application/octet-stream',
                headers={'Content-Disposition':'attachment; '+file_name})

    @property
    def form_class(self):
        # Creates a form class if it is not declared
        if not self._form_class:
            self._form_class = modelform_factory(self.model, base_form=self.form, fieldsets=self.get_fieldsets(),
                    fields=self.get_fields(), exclude=self.exclude, readonly=self.get_readonly_fields())
            self._form_class.admin_module = self

        # Applies default redirection after saved
        if not getattr(self._form_class._meta, 'redirect_after_saved', None):
            self._form_class._meta.redirect_after_saved = '../'

        # Default templates path
        if not getattr(self._form_class._meta, 'template', None):
            self._form_class._meta.template = ('admin/%(app)s/%(module)s/form.html', 'admin/%(app)s/module_form.html', 'admin/module_form.html')

        return self._form_class

    @render_template(('admin/%(app)s/%(module)s/delete.html', 'admin/%(app)s/module_delete.html', 'admin/module_delete.html'))
    def delete_view(self, request, pk, **kwargs):
        try:
            obj = self.get_object(request, pk)
        except self.model.DoesNotExist:
            raise Http404(request)

        if request.method == 'POST' and request.POST['confirm']:
            obj.delete()
            return HttpResponse(redirect_to(request, request.path_info + '../../'))
        return {'object':obj, 'request':request, 'object_verbose_name': obj._meta.verbose_name}

    def get_queryset(self, request):
        return self.model.query()

    def get_object(self, request, pk):
        return self.model.query().get(pk=pk)

    def get_columns(self, request, sorted):
        def col_dict(name):
            ret = {'name':name, 'title':make_title(name)}
            if name in self.model._meta.fields:
                field = self.model._meta.fields[name]
                ret['title'] = unicode(field.verbose_name or make_title(name))
                ret['type'] = field.base_type
            # compose URL for columns to make a sort: saves current GET params and add new for sorting
            ret['sort_url'] = request.path_info+"?%ssortby=%s&order=%s" % ('&'.join(["%s=%s" % (key, val) for key, val in request.GET.items()])+"&" if '?' in request.get_full_path() else '', name, 'asc' if sorted.get('order', None) == "desc" else "desc")
            return ret
        return [col_dict(name) for name in self.list_display]

    def get_fieldsets(self):
        return self.fieldsets

    def get_fields(self):
        if self.fieldsets:
            return reduce(lambda a,b:a+b, [fs['fields'] for fs in self.fieldsets])
        return self.fields

    def get_readonly_fields(self):
        return self.readonly_fields

