import copy

from london.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpRequest
from london.forms.fields import Field, FileField
from london.forms.widgets import Widget, Media, media_property
from london.templates import get_template_env, render_base, render_to_string
from london.templates.signals import template_global_context
from london.exceptions import TemplateNotFound, ValidationError, IgnoreField
from london.utils.datastructures import SortedDict

from jinja2.exceptions import TemplateNotFound as JinjaTemplateNotFound

NON_FIELD_ERRORS = '__all__'


class FieldRenderer(object):
    def __init__(self, renderer, field, widget, errors=None):
        self._renderer = renderer
        self._field = field
        self._widget = widget
        self._errors = errors

    def __unicode__(self):
        return self.widget

    def __getitem__(self, key):
        # This must be __getitem__ instead of __getattr__ to avoid conflicts and circular reference
        if key == 'value':
            return self._renderer.initial.get(self._field.name, '')

        return getattr(self._field, key)

    @property
    def render(self):
        return u'<div class="%(name)s">%(label_tag)s %(widget)s %(help_box)s %(errors)s</div>'%{
                'name': self._get_field_name(),
                'widget': self.widget,
                'label_tag': self.label_tag,
                'errors': self.errors,
                'help_box': self.help_box,
                }

    @property
    def label_tag(self):
        return self._widget.render_label(name=self._field.name, label=self._field.get_label())

    @property
    def widget(self):
        if not getattr(self._widget, 'input_value_is_valid', False) and hasattr(self._field, 'input_value'):
            value = self._field.input_value
        else:
            value = self._renderer.initial.get(self._field.name, None)
            value = self._field.prepare_value(value)
        return self._widget.render(name=self._get_field_name(), value=value)

    @property
    def errors(self):
        return self._widget.render_errors(name=self._get_field_name(), errors=self._errors)

    @property
    def help_box(self):
        return self._widget.render_help_box(name=self._field.name, help_text=self._field.help_text)

    def _get_field_name(self):
        return  self._renderer.prefix + self._field.name


class ErrorList(list):
    key = None

    def __init__(self, key, errors):
        self.key = key
        super(ErrorList, self).__init__(errors)

    def __unicode__(self):
        if not self:
            return ''
        
        errors = []
        for row in self:
            errors.append('<li>%s</li>' % row)
        return '<ul class="errors" for="%s">%s</ul>' % (self.key, ''.join(errors))


class ErrorDict(dict):
    def __unicode__(self):
        if not self:
            return ''

        errors = []
        for k,v in self.items():
            for row in v:
                errors.append('<li class="%s">%s</li>'%(k,row))
        return '<ul class="errors">%s</ul>'%''.join(errors)

    def __setitem__(self, key, value):
        if not isinstance(value, ErrorList):
            value = ErrorList(key, value)
        super(ErrorDict,self).__setitem__(key, value)

    def setdefault(self, key, value):
        if not isinstance(value, ErrorList):
            value = ErrorList(key, value)
        super(ErrorDict,self).setdefault(key, value)


class FormRenderer(object):
    """
    This class does the job of render the given for to HTML syntax, using widgets for the form fields.
    """
    form = None
    initial = None
    prefix = ''

    def __init__(self, form, initial, prefix=None):
        self.form = form
        self.initial = initial
        self.prefix = prefix or self.prefix

        if getattr(self.form, 'request', None):
            self.path_info = self.form.request.path_info

    def render(self):
        ret = []

        # Errors
        if self.non_field_errors:
            ret.append(self.non_field_errors)

        if getattr(self.form._meta, 'fieldsets', None):
            for fs in self.form._meta.fieldsets:
                fs_html = []
                if fs.get('label',None):
                    fs_html.append('<h3>%s</h3>' % fs['label'])

                # Attributes
                attrs = fs.get('attrs', {})
                attrs = ' '.join(['%s=%s'%(name,value) for name,value in attrs])

                for field in fs['fields']:
                    fs_html.append(self[field].render)

                ret.append('<fieldset %s>%s</fieldset>' % (attrs, ''.join(fs_html)))

        else:
            # Fields
            for field in self.fields:
                ret.append(field.render)
            
        return u''.join(ret)
    
    @property
    def media(self):
        """
        Provide a description of all media required to render the widgets on this form
        """
        media = Media()
        for field in self.form.fields.values():
            media = media + field.widget.media
        return media

    def render_label(self, field, widget):
        return widget.render_label(name=field.name, label=field.get_label())

    def __unicode__(self):
        return self.render()

    def __str__(self):
        return unicode(self)
    
    @property
    def errors(self):
        return self.form.errors or ''

    @property
    def non_field_errors(self):
        if not self.form.errors or not self.form.errors.get(NON_FIELD_ERRORS, []):
            return ''
        return '<ul class="errors">%s</ul>'%''.join(['<li>%s</li>'%msg for msg in self.form.errors[NON_FIELD_ERRORS]])

    @property
    def fields(self):
        try:
            # The Meta attribute "fields_order" is useful to set the right order of fields in the form when rendering
            field_names = self.form._meta.fields_order
        except AttributeError:
            # If the fields order wasn't declared, uses the fields keys as default
            field_names = self.form.fields.keys()

        for name in field_names:
            yield self[name]

    def __getitem__(self, name):
        # This must be __getitem__ instead of __getattr__ to avoid conflicts and circular reference
        field = self.form.fields[name]
        widget = field.get_widget(form=self.form)
        widget.readonly = field.readonly
        return FieldRenderer(self, field, widget, self.form.errors.get(name) if self.form.errors else None)


class BaseForm(HttpResponse):
    """
    This is the base class for form views, used instead of views for form URLs.
    """

    request = None
    renderer = FormRenderer
    _errors = None
    _only_informed_fields = False

    def __new__(cls, *args, **kwargs):
        _view_wrapper = getattr(cls, '_view_wrapper', None)
        if _view_wrapper:
            if args and isinstance(args[0], HttpRequest):
                request = args[0]
            else:
                request = kwargs.get('request', None)

            resp = _view_wrapper(request)
            if resp:
                return resp

        return super(BaseForm, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], HttpRequest):
            self.request = args[0]
            args = args[1:]
        else:
            self.request = kwargs.pop('request', None)

        self.view_args = args
        self.view_kwargs = kwargs

        super(BaseForm, self).__init__()

        # Creates instance fields (to prevent the usage of self._meta.fields that is just for class purposes)
        self.fields = copy.deepcopy(self._meta.fields)

        # Calls the function to initialize the form (in special the instance fields)
        self.initialize()

        # Running HTTP methods
        if self.request and kwargs.get('execute',True):
            self.execute()

    def initialize(self):
        """Fields, widgets and other initilization procedures must come here."""
        pass

    def execute(self):
        ajax_or_http = 'ajax' if self.request.is_ajax() else 'http'
        internal_method = '_%s_%s'%(ajax_or_http, self.request.method.lower())
        self.content = getattr(self, internal_method)(*self.view_args, **self.view_kwargs)

    def default_context(self, *args, **kwargs):
        return {}

    def default_response(self, context, *args, **kwargs):
        if isinstance(context, (HttpResponse, basestring)):
            return context

        for t_context in template_global_context.send(request=self.request):
            context.update(t_context)
        context.update(self.default_context(*args, **kwargs))
        context['form'] = self.get_renderer(form=self, initial=self.get_initial())

        template = kwargs.get('template', self._meta.template)
        return render_to_string(template, context, theme=getattr(self.request,'theme',None),
                is_ajax=self.request.is_ajax(), http_kwargs=kwargs)

    def _http_head(self, *args, **kwargs):
        return HttpResponse('')

    def _http_delete(self, *args, **kwargs):
        return HttpResponseNotAllowed(('head','post','get'))

    def _http_get(self, *args, **kwargs):
        if hasattr(self, 'http_get'):
            context = self.http_get(*args, **kwargs) or {}
        else:
            context = {}

        if isinstance(context, HttpResponse):
            return context

        content = self.default_response(context, *args, **kwargs)

        return render_base(content, context)

    def _http_post(self, *args, **kwargs):
        if hasattr(self, 'http_post'):
            context = self.http_post(*args, **kwargs) or {}
        else:
            context = {}

        if isinstance(context, HttpResponse):
            return context

        return self.default_response(context, *args, **kwargs)

    def _ajax_get(self, *args, **kwargs):
        if hasattr(self, 'ajax_get'):
            context = self.ajax_get(*args, **kwargs) or {}
        else:
            context = {}

        if self._meta.ajax_get_json_response:
            resp = {'fields':self.fields.keys()}
            if self.errors:
                resp['errors'] = self.errors
            return JsonResponse(resp)

        if isinstance(context, HttpResponse):
            return context

        content = self.default_response(context, *args, **kwargs)

        if not content.strip().startswith('<!doctype html>') and '<base ' in content:
            # This code ensures the code will reload as a direct URL instead of Ajax in a history
            # getting back from an outside page
            content = '<script>window.location = \'%s\';</script>'%self.request.path_info + content

        return content

    def _ajax_post(self, *args, **kwargs):
        if hasattr(self, 'ajax_post'):
            context = self.ajax_post(*args, **kwargs) or {}

            if isinstance(context, str):
                return context
        else:
            context = {}

        if self._meta.ajax_post_json_response:
            resp = {'fields':self.fields.keys()}
            if self.errors:
                resp['errors'] = self.errors
            return JsonResponse(resp)

        if isinstance(context, HttpResponse):
            return context

        content = self.default_response(context, *args, **kwargs)

        if not content.strip().startswith('<!doctype html>') and '<base ' in content:
            # This code ensures the code will reload as a direct URL instead of Ajax in a history
            # getting back from an outside page
            content = '<script>window.location = \'%s\';</script>'%self.request.path_info + content

        return content

    def get_initial(self, initial=None):
        initial = initial or {}

        # Initial default, coming from fields attribute "initial"
        for name,field in self.fields.items():
            if field.initial is not None:
                initial[name] = field.initial

        # Initial values comming from cleaned_data, if that's the case
        if getattr(self, 'cleaned_data', None):
            for name,value in self.cleaned_data.items():
                field = self.fields.get(name, None)
                if value is not None and field and field.returns_initial:
                    initial[name] = value

        return initial

    def get_renderer(self, form=None, initial=None):
        form = form or self
        initial = initial or {}
        return self.renderer(form=form, initial=initial)

    def is_valid(self, only_informed_fields=False):
        self._only_informed_fields = only_informed_fields
        if not getattr(self, 'cleaned_data', None):
            self.full_clean()
        return not bool(self._errors)

    def full_clean(self):
        self._errors = ErrorDict()
        self.cleaned_data = {}
        self.changed_data = {}

        self.clean_before()

        if self._clean_fields():
            self._clean_form()

        if self._errors:
            del self.cleaned_data

    def _clean_fields(self):
        initial = self.get_initial()

        for name, field in self.fields.items():
            if field.readonly or (self._only_informed_fields and name not in self.data):
                continue

            widget = field.get_widget(form=self)
            widget.readonly = field.readonly
            value = widget.value_from_datadict(self.data, self.files, name) # FIXME: the prefix
            if name in self.data:
                field.input_value = self.data[name]

            try:
                # Initializes empty
                self.cleaned_data[name] = None

                # Gets and cleans value using field clean method or initial data

                if isinstance(field, FileField):
                    value = field.clean(value, initial.get(name, field.initial))
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value

                # Sets the changed data dictionary
                if self.cleaned_data[name] != initial.get(name, None):
                    self.changed_data[name] = self.cleaned_data[name]

                # Calls the field cleaner declared as form method
                if hasattr(self, 'clean_'+name) and callable(getattr(self, 'clean_'+name)):
                    self.cleaned_data[name] = getattr(self, 'clean_'+name)()
                    
                widget.input_value_is_valid = True
            except ValidationError as e:
                error_field_name = e.field_name or name
                self._errors.setdefault(error_field_name, [])
                self._errors[error_field_name].append(e.message)
            except IgnoreField:
                continue

        return not bool(self._errors)

    def _clean_form(self):
        try:
            self.cleaned_data = self.clean()
        except ValidationError as e:
            error_field_name = e.field_name or NON_FIELD_ERRORS
            self._errors.setdefault(error_field_name, [])
            self._errors[error_field_name].append(e.message)

    def clean_before(self):
        pass

    def clean(self):
        return self.cleaned_data
    
    @property
    def errors(self):
        return self._errors

    @property
    def data(self):
        return self.request.POST if self.request.method in ('POST','PUT') else self.request.GET

    @property
    def files(self):
        return self.request.FILES

    def has_file_fields(self):
        return bool([f for f in self.fields.values() if f.is_file_field])

class FormMeta(object):
    ajax_get_json_response = False
    ajax_post_json_response = False
    fieldsets = None

    def __init__(self, form):
        meta = getattr(form, 'Meta', None)
        if meta:
            for attr in dir(meta):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(meta, attr))

class FormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if bases[0] != BaseForm:
            fields = []
            for attr, obj in attrs.items():
                if not isinstance(obj, Field): continue
                obj.name = attr
                fields.append((attr, attrs.pop(attr)))
            fields.sort(key=lambda x: x[1].creation_counter)
            fields = SortedDict(fields)

        new_class = super(FormMetaclass, cls).__new__(cls, name, bases, attrs)

        if bases[0] != BaseForm:
            new_class._meta = FormMeta(new_class)
            new_class._meta.fields = fields
            
            if 'media' not in attrs:
                new_class.media = media_property(new_class)

        return new_class

class Form(BaseForm):
    __metaclass__ = FormMetaclass

