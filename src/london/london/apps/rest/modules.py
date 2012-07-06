import decimal
import datetime
import hashlib

from london.urls import patterns
from london.forms.models import modelform_factory, ModelFormMetaclass, BaseModelForm
from london.utils.strings import make_title
from london.http import JsonResponse, Http404
from london.db.models import PersistentModel
from london.exceptions import ObjectDoesNotExist
from london.db.models.querysets import ManyToManyQuerySet
from london.apps.cache import cache
from london.apps.rest import app_settings

JSON_RECOGNIZED_TYPES = (basestring, int, float, bool, list, tuple, dict, decimal.Decimal,
        datetime.datetime, datetime.date, datetime.time)

class InvalidMethod(Exception): pass

class BaseModuleForm(BaseModelForm):
    __metaclass__ = ModelFormMetaclass

class BaseModule(object):
    name = None
    title = None

    def __init__(self, site=None, request=None):
        self.site = site
        self.request = request

    def __unicode__(self):
        return self.title or self.name.title()

    def get_title(self):
        return self.title or make_title(self.name)

    @property
    def url(self):
        return '%s%s/'%(self.site.root_url, self.name)

    def get_urls(self):
        return patterns()

class CrudModule(BaseModule):
    model = None
    form = None
    list_fields = None
    view_fields = None
    editable_fields = None
    search_fields = None
    max_results = 20

    def __init__(self, site=None, request=None):
        super(CrudModule, self).__init__(site, request)
        self.name = self.name or self.model.__name__.lower() # Change this to "model.verbose_name"
        self.list_fields = self.list_fields or self.view_fields
        self.view_fields = self.view_fields or self.list_fields

    def get_urls(self):
        return patterns('',
                (r'^$', self.site.auth_required(self.list_view), {}, '%s_%s_list'%(self.site.root_prefix, self.name)),
                (r'^search/$', self.site.auth_required(self.search_view), {}, '%s_%s_search'%(self.site.root_prefix, self.name)),
                (r'^add/$', self.site.auth_required(self.object_view), {}, '%s_%s_add'%(self.site.root_prefix, self.name)),
                (r'^(?P<key>\w+)/$', self.site.auth_required(self.object_view), {}, '%s_%s_edit'%(self.site.root_prefix, self.name)),
                )

    def list_view(self, request, **kwargs):
        fields = self.list_fields or ['pk']
        qs = self.get_queryset(request)

        if request.GET:
            criteria = dict([(k,request.GET[k]) for k in request.GET.keys() if not k.startswith('_')])
            qs = qs.filter(**criteria)

        qs = qs.values(*fields)

        max_results = min([int(request.GET.get('_max', self.max_results)), self.max_results])
        if max_results:
            qs = qs[:max_results]

        return JsonResponse([self.prepare_for_json(obj) for obj in qs])

    def make_search_cache_key(self, q):
        # Query string hash 
        hsh = hashlib.md5(q).hexdigest()

        return app_settings.CACHE_KEY_PREFIX + '%s:%s'%(self.model._meta.path_label, hsh)

    def search_view(self, request, **kwargs):
        fields = self.list_fields or ['pk']
        q = request.GET.get('q', None)
        qs = []

        # Makes the cache key
        cache_key = self.make_search_cache_key(q)

        # Tries to return from cache first
        from_cache = cache.get(cache_key)
        if from_cache:
            return JsonResponse(from_cache)

        if q and self.search_fields:
            # Basic query
            qs = self.get_queryset(request)

            # Filter by query string
            criteria = dict([(k+'__icontains',q) for k in self.search_fields])
            qs = qs.filter_if_any(**criteria)

            # Converts to values
            qs = qs.values(*fields)

            # Limited list results
            max_results = min([int(request.GET.get('_max', self.max_results)), self.max_results])
            if max_results:
                qs = qs[:max_results]

        # Prepares for JSON and to store in cache
        results = [self.prepare_for_json(obj) for obj in qs]
        if app_settings.CACHE_TIMEOUT:
            cache.set(cache_key, results, app_settings.CACHE_TIMEOUT)

        return JsonResponse(results)

    def object_view(self, request, **kwargs):
        key = kwargs.get('key', None)
        if request.method not in ('GET','PUT','POST','DELETE') or (request.method in ('GET','DELETE') and key is None):
            raise InvalidMethod('The method "%s" with key "%s" is invalid for this object resource'%(request.method,key))

        try:
            obj = self.get_object(request, key) if key else None
        except ObjectDoesNotExist:
            res = {'result':'error', 'message': 'Object not found.'}
        else:
            if request.method in ('PUT','POST') and not key:
                obj, res = self.rest_object_add(request, kwargs)
            elif request.method in ('PUT','POST') and key:
                obj, res = self.rest_object_change(request, obj, kwargs)
            elif request.method == 'GET':
                obj, res = self.rest_object_get(request, obj, kwargs)
            elif request.method == 'DELETE':
                obj, res = self.rest_object_delete(request, obj, kwargs)
            else:
                res = {'result':'error', 'message':'Unrecognized URL and method.'}

        return JsonResponse(res or {})

    def rest_object_add(self, request, kwargs):
        return self.rest_object_change(request, None, kwargs)

    def rest_object_change(self, request, obj, kwargs):
        if not self.editable_fields:
            raise Http404
        form = self.form_class(request=request, execute=False, instance=obj)
        if form.is_valid(only_informed_fields=True):
            obj = form.save()
            return obj, {'pk': unicode(obj['pk'])}
        else:
            return obj, {'result':'error', 'messages':form.errors}

    def rest_object_get(self, request, obj, kwargs):
        if not self.view_fields:
            raise Http404
        values = dict([(f, obj[f]) for f in self.view_fields])
        return obj, self.prepare_for_json(values)

    def rest_object_delete(self, request, obj, kwargs):
        obj.delete()
        return obj, {'pk': unicode(obj['pk'])}

    def prepare_for_json(self, values):
        for key, value in values.items():
            try:
                values[key] = getattr(self, 'get_%s_value')(value)
            except AttributeError:
                if isinstance(value, PersistentModel):
                    values[key] = {'pk':unicode(value['pk']), 'display': unicode(value)}
                elif isinstance(value, ManyToManyQuerySet):
                    objects = values[key]
                    values[key] = [{'pk':str(obj['pk']), 'display':unicode(obj)} for obj in objects]
                elif not isinstance(value, JSON_RECOGNIZED_TYPES) and value is not None:
                    values[key] = unicode(value)
        return values

    def get_queryset(self, request):
        return self.model.query()

    def get_object(self, request, pk):
        return self.model.query().get(pk=pk)

    @property
    def form_class(self):
        if not self.form:
            self.form = modelform_factory(self.model, base_form=BaseModuleForm, fields=self.editable_fields)

        return self.form

