from london.db import models
from london.db.utils import get_related_class
from london.forms.base import BaseForm, FormMetaclass, FormRenderer, media_property
from london.forms import fields, widgets, formsets
from london.core.files.uploadedfile import UploadedFile
from london.db.models.fields.files import FieldFile
from london.http import Http404
from london.apps.ajax.tags import redirect_to
from london.exceptions import ObjectDoesNotExist


class ModelFormRenderer(FormRenderer):
    def __init__(self, *args, **kwargs):
        super(ModelFormRenderer, self).__init__(*args, **kwargs)
        self.instance = getattr(self.form, 'instance', None)


class BaseModelForm(BaseForm):
    instance = None
    renderer = ModelFormRenderer
    saved = False

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', self.instance)
        super(BaseModelForm, self).__init__(*args, **kwargs)

    def get_initial(self, initial=None):
        initial = initial or {}

        if self.instance:
            for name, field in self.fields.items():
                initial[name] = self.instance.get(name, None)
        else:
            for name, field in self.fields.items():
                if field.initial is not None:
                    initial[name] = field.initial

        if getattr(self, 'data', None):
            initial = super(BaseModelForm, self).get_initial(initial)

        return initial

    def _http_delete(self, *args, **kwargs):
        if not getattr(self._meta, 'delete_method', False):
            return HttpResponseNotAllowed(('head','post','get'))

    def _http_get(self, *args, **kwargs):
        try:
            self.instance = self.get_instance(*args, **kwargs)
        except self._meta.model.DoesNotExist:
            raise Http404
        return super(BaseModelForm, self)._http_get(*args, **kwargs)

    def _ajax_get(self, *args, **kwargs):
        try:
            self.instance = self.get_instance(*args, **kwargs)
        except self._meta.model.DoesNotExist:
            raise Http404
        return super(BaseModelForm, self)._ajax_get(*args, **kwargs)

    def _http_post(self, *args, **kwargs):
        try:
            self.instance = self.get_instance(*args, **kwargs)
        except self._meta.model.DoesNotExist:
            raise Http404

        if self.is_valid():
            self.save()
            return redirect_to(self.request, getattr(self._meta, 'redirect_after_saved', '..'))

        return super(BaseModelForm, self)._http_post(*args, **kwargs)

    def _ajax_post(self, *args, **kwargs):
        try:
            self.instance = self.get_instance(*args, **kwargs)
        except self._meta.model.DoesNotExist:
            raise Http404

        if self.is_valid():
            self.save()
            return redirect_to(self.request, getattr(self._meta, 'redirect_after_saved', '..'))

        return super(BaseModelForm, self)._ajax_post(*args, **kwargs)

    def get_instance(self, pk=None, *args, **kwargs):
        obj = self._meta.model.query().get(pk=pk) if pk else self._meta.model()
        return obj

    def save(self, commit=True, force_new=False):
        self.instance = self.instance or self._meta.model()

        for key, value in self.cleaned_data.items():
            # WAS: if key not in self._meta.model._meta.fields or (self._only_informed_fields and key not in self.data):
            if key not in self._meta.model._meta.fields or key not in self._meta.fields or (self._only_informed_fields and key not in self.data):
                continue

            db_field = self._meta.model._meta.fields[key]

            if isinstance(value, UploadedFile):
                self.instance[key] = db_field.attr_class(self.instance, db_field, value.name)
                self.instance[key].save(value.name, value, save=False)
            elif isinstance(db_field, models.PasswordField):
                # Doesn't set this field if it is None (not changed)
                if value:
                    self.instance[key] = value
            else:
                self.instance[key] = value

        if force_new:
            self.instance.clear_pk()

        if commit:
            self.instance.save()
            self.saved = True

        return self.instance


def form_field_for_db_field(field, parent_model):
    """
    Returns the equivalent form field for a given DB field.
    """
    if isinstance(field, models.TextField):
        return fields.TextField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.PasswordField):
        return fields.PasswordField(max_length=field.max_length, required=not field.blank,
                algorithm=field.algorithm, help_text=field.help_text, label=field.verbose_name)
    elif isinstance(field, models.FileField):
        return fields.FileField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.CharField):
        kwargs = {
            'max_length': field.max_length,
            'required': not field.blank,
            'initial': field.default,
            'help_text': field.help_text,
            'label': field.verbose_name,
            'force_lower_case': field.force_lower_case,
            'force_upper_case': field.force_upper_case,
            }
        if field.choices:
            choices = ([('', '-'*10)] if field.blank else []) + list(field.choices)
            kwargs['widget'] = widgets.Select(choices=field.choices)
        return fields.CharField(**kwargs)
    elif isinstance(field, models.BooleanField):
        return fields.BooleanField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.ForeignKey):
        return ModelChoiceField(queryset=field.get_related_queryset, parent_model=parent_model,
                required=not field.blank, help_text=field.help_text, label=field.verbose_name)
    elif isinstance(field, models.NestedListField):
        formset_class = nestedmodelformset_factory(from_dbfield=field, parent_model=parent_model)
        return formset_class(required=not field.blank)
    elif isinstance(field, models.ManyToManyField):
        return ModelMultipleChoiceField(queryset=field.get_related_queryset, parent_model=parent_model,
                required=not field.blank, help_text=field.help_text, label=field.verbose_name)
    elif isinstance(field, models.DecimalField):
        return fields.DecimalField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name, max_digits=field.max_digits, decimal_places=field.decimal_places)
    elif isinstance(field, models.MoneyField):
        return fields.MoneyField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.IntegerField):
        return fields.IntegerField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.DateField):
        return fields.DateField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.TimeField):
        return fields.TimeField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    elif isinstance(field, models.DateTimeField):
        return fields.DateTimeField(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)
    else:
        return fields.Field(required=not field.blank, initial=field.default, help_text=field.help_text,
                label=field.verbose_name)


class ModelFormMetaclass(FormMetaclass):
    def __new__(cls, name, bases, attrs):
        if bases[0] != BaseModelForm:
            # Gets field names with excluded fields. If there is not attribute for that, gets
            # from model fields
            field_names = ('Meta' in attrs and getattr(attrs['Meta'], 'fields', None)) or\
                          attrs['Meta'].model._meta.fields.keys()
            for exc in (('Meta' in attrs and getattr(attrs['Meta'], 'exclude', None)) or []):
                if exc in field_names:
                    field_names.remove(exc)
            readonly_fields = getattr(attrs['Meta'], 'readonly', [])

            fields = {}

            # Form fields
            if hasattr(bases[0], '_meta') and getattr(bases[0]._meta, 'fields', None):
                fields.update(bases[0]._meta.fields)

            # Model fields
            for f_name in field_names:
                if not attrs.get(f_name, None):
                    if f_name in attrs['Meta'].model._meta.fields:
                        field = attrs['Meta'].model._meta.fields[f_name]
                        fields[f_name] = form_field_for_db_field(field, attrs['Meta'].model)
                        fields[f_name].readonly = f_name in (readonly_fields or [])

            attrs.update(fields)

        new_class = super(ModelFormMetaclass, cls).__new__(cls, name, bases, attrs)
        
        if bases[0] != BaseModelForm:
            if hasattr(attrs['Meta'], 'fields_order'):
                new_class._meta.fields_order = attrs['Meta'].fields_order

        if 'media' not in attrs:
            new_class.media = media_property(new_class)

        return new_class


class ModelForm(BaseModelForm):
    __metaclass__ = ModelFormMetaclass


def modelform_factory(model, base_form=ModelForm, fields=None, exclude=None, readonly=None, fieldsets=None):
    field_names = fields or model._meta.fields.keys()
    meta_attrs = {'model':model, 'fields':field_names, 'exclude':exclude, 'readonly':readonly, 'fieldsets':fieldsets}
    meta = type('Meta', (object,), meta_attrs)
    return ModelFormMetaclass('%sForm'%model.__name__, (base_form,), {'Meta':meta})


class NestedModelFormsetMetaclass(formsets.NestedFormsetMetaclass):
    def __new__(cls, name, bases, attrs):
        if bases[0] != formsets.BaseNestedFormset:
            # Gets field names with excluded fields. If there is not attribute for that, gets
            # from model fields
            field_names = ('Meta' in attrs and getattr(attrs['Meta'], 'fields', None)) or\
                          attrs['Meta'].model._meta.fields.keys()
            for exc in (('Meta' in attrs and getattr(attrs['Meta'], 'exclude', None)) or []):
                if exc in field_names:
                    field_names.remove(exc)
            readonly_fields = getattr(attrs['Meta'], 'readonly', [])

            fields = {}
            for f_name in field_names:
                field = attrs['Meta'].model._meta.fields[f_name]
                fields[f_name] = form_field_for_db_field(field, attrs['Meta'].model)
                fields[f_name].readonly = f_name in (readonly_fields or [])

            attrs.update(fields)

        new_class = super(NestedModelFormsetMetaclass, cls).__new__(cls, name, bases, attrs)
        return new_class


class NestedModelFormset(formsets.BaseNestedFormset):
    __metaclass__ = NestedModelFormsetMetaclass

    def __init__(self, *args, **kwargs):
        super(NestedModelFormset, self).__init__(*args, **kwargs)
        self.form = None

    def get_form(self):
        if not self.form:
            self.form = modelform_factory(self._meta.model, fields=self._meta.fields,
                    readonly=self._meta.readonly)
        return self.form


def nestedmodelformset_factory(model=None, from_dbfield=None, parent_model=None,
        base_form=NestedModelFormset, fields=None, exclude=None, readonly=None):
    model = model if model else get_related_class(from_dbfield, parent_model)
    field_names = fields or model._meta.fields.keys()
    meta_attrs = {'model':model, 'fields':field_names, 'exclude':exclude, 'readonly':readonly}
    meta = type('Meta', (object,), meta_attrs)

    return type('%sFormset'%model.__name__, (base_form,), {'Meta':meta})


# Widgets

class ModelSelect(widgets.Select):
    def get_selected(self, value, key):
        value = unicode(value) if value else ''
        return ' selected="selected"' if value == key else ''


class ModelMultiSelect(widgets.CheckboxSelectMultiple):
    def get_selected(self, value, key):
        return ' checked="checked"' if key in map(unicode, value or []) else ''


# Fields

class BaseModelField(fields.ChoiceField):
    queryset = None
    parent_model = None

    def __init__(self, queryset, parent_model=None, **kwargs):
        self.queryset = queryset
        self.parent_model = parent_model or queryset.model
        super(BaseModelField, self).__init__(**kwargs)
 
    def get_queryset(self):
        return self.queryset(self.parent_model) if callable(self.queryset) else self.queryset

    def __deepcopy__(self, memo):
        obj = super(BaseModelField, self).__deepcopy__(memo)
        if isinstance(self.queryset, models.QuerySet):
            obj.queryset = self.queryset._clone()
        return obj


class ModelChoiceField(BaseModelField):
    widget = ModelSelect
    accept_not_found = False

    def clean(self, value):
        if value not in ('',None):
            try:
                value = self.get_queryset().get(pk=value)
            except ObjectDoesNotExist:
                # If this field accepts not found objects, probably some customized clean_field method will deal with it
                if not self.accept_not_found:
                    raise

        return value

    def prepare_value(self, value):
        """Prepare the given value to be rendered for the form."""
        if isinstance(value, basestring) or value is None:
            return value
        else:
            return value['pk']

    def get_choices(self):
        queryset = self.get_queryset()

        choices = [(unicode(obj['pk']), unicode(obj)) for obj in queryset]
        if not self.required and len([c for c in choices if not c[0]]) == 0:
            choices.insert(0, ('', self.empty_string))
        return choices


class ModelMultipleChoiceField(BaseModelField):
    widget = ModelMultiSelect

    def clean(self, value):
        if value is not None:
            value = self.get_queryset().filter(pk__in=value)
        return value

    def prepare_value(self, value):
        """Prepare the given value to be rendered for the form."""
        if value is not None:
            value = [v['pk'] for v in value]
        return value

    def get_choices(self):
        return [(unicode(obj['pk']), unicode(obj)) for obj in self.get_queryset()]

