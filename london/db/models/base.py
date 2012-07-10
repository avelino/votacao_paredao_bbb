import os
import hashlib

from london.db.signals import model_get, model_save, model_delete, model_get_pk, model_clear_pk, pre_save, post_save, pre_delete, post_delete
from london.db.signals import model_list, model_list_delete, model_list_count, model_set_dependent, model_unset_dependent, model_get_dependents
from london.db import _registered_models, _external_relations
from london.conf import settings
from london.db.connections import get_connection
from london.db.models.querysets import BaseQuerySet
from london.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, DuplicatedUniqueIndex, ObjectHasDependents
from london.utils.imports import import_anything
from london.utils.datastructures import SortedDict
from london.utils.strings import split_title

from fields import *

# Starts all available connections
# FIXME: this has to be improved to open only needed connections
for db in settings.DATABASES:
    get_connection(db)

class ModelMeta(object):
    abstract = False
    db_storage = None
    app_label = None
    model_label = None
    verbose_name = None
    verbose_name_plural = None
    query = 'london.db.models.QuerySet'
    unique_together = None # A tuple of tuples
    indexes = None # A tuple of fields
    permissions = None # A tuple of tuples
    abstract = False
    ordering = None

    def __init__(self, model):
        meta = getattr(model, 'Meta', None)
        if meta:
            for attr in dir(meta):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(meta, attr))

        model_name_bits = model.__module__.split('.')
        if len(model_name_bits) > 1: model_name_bits.pop()
        self.app_label = self.app_label or model_name_bits[-1].lower()

        self.model_label = self.model_label or model.__name__
        self.db_storage = self.db_storage or '%s_%s'%(self.app_label, model.__name__.lower())
        self.verbose_name = self.verbose_name or split_title(model.__name__)
        self.verbose_name_plural = self.verbose_name_plural or (self.verbose_name + 's')
        self.unique_together = self.unique_together or []
        self.indexes = self.indexes or []
        self.permissions = self.permissions or []
        self.ordering = self.ordering or []

    def add_external_relation(self, field, class_from, related_name, bound_queryset_function):
        _external_relations.setdefault(field.related, {})
        _external_relations[field.related][related_name] = bound_queryset_function

class LazyLoadingObject(object):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, inst2):
        return not self.__eq__(inst2)

class BaseModel(object):
    _old_values = None
    _new_values = None
    _deleted = False
    _deleted_values = None
    _nested_into = None
    _old_hash = None
    _external_relations = None

    def __new__(cls, **kwargs):
        obj = super(BaseModel, cls).__new__(cls)

        for name, field in obj._meta.fields.items():
            if hasattr(field, 'contribute_to_object'):
                field.contribute_to_object(obj)

        return obj

    def __init__(self, **kwargs):
        _set_old_values = kwargs.pop('_set_old_values', False)
        self._nested_into = kwargs.pop('_nested_into', None)

        # Field values from kwargs
        values = dict([(key, self.clean_field_value(key, value)) for key,value in kwargs.items()])

        self._old_values = dict([(key,None) for key in self._meta.fields.keys()])
        self._new_values = {}
        self._deleted_values = []

        if _set_old_values:
            self._old_values.update(values)
        else:
            self._new_values = values

            # Default field values
            for key,field in self._meta.fields.items():
                if key not in values:
                    default = field.get_default(self)
                    if default is not None or field.null:
                        values[key] = default

        self._old_hash = self.make_hash()

        # Starts external relations
        self._external_relations = dict()
        self.clear_external_relations()

        # Sets dependencies
        for key, value in self._new_values.items():
            self.set_dependent(key, value)

    def __repr__(self):
        return '<%s "%s">' % (self._meta.path_label, unicode(self['pk']))

    def __unicode__(self):
        return '%s # %s' % (self._meta.path_label, self['pk'])

    def clear_external_relations(self, names=None):
        # Makes clones for declared external relations (they are empty queryset instances)
        for name, func in _external_relations.get(self._meta.path_label, {}).items():
            if not names or name in names:
                self._external_relations[name] = func

    def __eq__(self, inst2):
        return isinstance(inst2, self.__class__) and inst2['pk'] == self['pk']

    def __ne__(self, inst2):
        return not self.__eq__(inst2)

    def __setitem__(self, key, value):
        # TODO: deal with the conflict '_id' vs 'pk' for MongoDB and similar situations on other databases
        self._new_values[key] = self.clean_field_value(key, value, force_lazy_to_load=True)

        # Calls signals to set and unset dependencies if this is a ForeignKey field
        self.set_dependent(key, value)

        # Removes stored deletion for this field
        if key in self._deleted_values:
            self._deleted_values.remove(key)

    def set_dependent(self, key, value):
        if key in self._meta.fields and isinstance(self._meta.fields[key], ForeignKey) and \
           self._new_values[key] != self._old_values.get(key, None):
            if self._old_values.get(key, None):
                model_unset_dependent.send(dependent=self, depended=self._old_values[key], field=self._meta.fields[key])

            model_set_dependent.send(dependent=self, depended=self._new_values[key], field=self._meta.fields[key])

    def get_forcing_lazy(self, dic, key):
        if isinstance(dic[key], LazyLoadingObject):
            dic[key] = self.clean_field_value(key, dic[key].value, force_lazy_to_load=True)
        return dic[key]

    def __getitem__(self, key):
        if key == 'pk':
            return self.pk
        elif key in self._deleted_values:
            raise KeyError('Value for field "%s" was deleted.' % key)
        elif key in self._external_relations:
            # Storing external relations results in cache to avoid request it again
            if callable(self._external_relations[key]):
                self._external_relations[key] = self._external_relations[key](self)
            return self._external_relations[key]
        elif key in self._new_values:
            return self.get_forcing_lazy(self._new_values, key)
        elif key in self._old_values:
            return self.get_forcing_lazy(self._old_values, key)
        else:
            return None

    def __delitem__(self, key):
        self._deleted_values.append(key)

    def __getattr__(self, name):
        if name.startswith('get_') and name.endswith('_display'):
            name = name[4:-8]
            if name in self._meta.fields and self._meta.fields[name].choices:
                def get_field_display():
                    d = dict(self._meta.fields[name].choices)
                    return d[self[name]] if self[name] else ''
                return get_field_display
        raise AttributeError("'%s' object has no attribute '%s'"%(self.__class__.__name__, name))

    def get(self, key, default):
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key, value):
        self[key] = value
    
    def get_values_to_save(self):
        values = {}
        values.update(self._new_values)

        for name,field in self._meta.fields.items():
            # Queryset values
            if name not in values and isinstance(self[name], BaseQuerySet) and self[name].has_changed():
                values[name] = self[name]

            # File fields values
            if field.is_file_field:
                values[name] = unicode(values[name].name) if values.get(name, None) else None

            # Auto value fields
            if callable(field.auto):
                try:
                    values[name] = field.auto(instance=self)
                except TypeError:
                    values[name] = field.auto()
                self[name] = values[name]

        # Convert lazy objects
        for k in values:
            if isinstance(values[k], LazyLoadingObject):
                self.get_forcing_lazy(values, k)

        return values

    def setdefault(self, key, value):
        self[key] = self.get(key, value)

    @property
    def pk(self):
        results = model_get_pk.send(instance=self)
        return results[0]

    def clean_field_value(self, key, value, force_lazy_to_load=False):
        """
        This method uses declared fields to validate a given key and value and clean them to be in
        the desirable formats and data types.
        """
        if key in self._meta.fields:
            field = self._meta.fields[key]
            if not field.lazy_load or force_lazy_to_load:
                return field.clean_value(self, value)
            elif field.lazy_load:
                return LazyLoadingObject(value)

        return value

    def as_dict(self, *fields, **kwargs):
        load_lazy = kwargs.get('load_lazy', True)
        d = {}

        # Old values
        for k in self._old_values:
            if not fields or k in fields:
                if load_lazy:
                    d[k] = self.get_forcing_lazy(self._old_values, k)
                else:
                    d[k] = self._old_values[k]

        # New values
        for k in self._new_values:
            if not fields or k in fields:
                if load_lazy:
                    d[k] = self.get_forcing_lazy(self._new_values, k)
                else:
                    d[k] = self._new_values[k]

        if 'pk' in fields:
            d['pk'] = self['pk']

        return d

    def has_changed(self):
        return self._old_hash != self.make_hash()

    def make_hash(self):
        return hashlib.sha1(unicode(self.as_dict(load_lazy=False))).hexdigest()

    def clear_pk(self):
        """Clears the object's primary key, usually for cloning this object."""
        model_clear_pk.send(instance=self)

    def clone(self, **field_values):
        to_save = field_values.pop('_save', True)
        current_values = self.as_dict()
        current_values.update(field_values)

        new = self.__class__(**current_values)
        new.clear_pk()

        if to_save:
            new.save()
        return new

    def get_all_dependents(self):
        """Returns a list with all objects with declared dependency on this object."""

        results = model_get_dependents.send(instance=self)
        results = reduce(lambda a,b: a+b, results) if results else []
        return results

class PersistentModel(BaseModel):
    _origin = None

    def __init__(self, **kwargs):
        _save = kwargs.pop('_save', False)
        self._origin = kwargs.pop('_origin', None)

        super(PersistentModel, self).__init__(**kwargs)

        if _save:
            self.save()

    @property
    def origin(self):
        return self._origin

    @classmethod
    def query(cls, **kwargs):
        query_class = import_anything(cls._meta.query)
        query = query_class(model=cls)

        if kwargs:
            query = query.filter(**kwargs)

        return query

    def save(self):
        self.validate_before_save()

        is_new = not bool(self['pk'])

        pre_save.send(instance=self, sender=self.__class__, new=is_new)
        ret = model_save.send(instance=self)
        post_save.send(instance=self, sender=self.__class__, new=is_new)

        self._old_values.update(self._new_values)
        self._new_values = {}
        self._old_hash = self.make_hash()

        return self

    def delete(self, force_if_has_dependents=False):
        # Checks dependents and block deletion if this object has anyone
        if not force_if_has_dependents:
            has_dependents = False
            for dep in self.get_all_dependents():
                has_dependents = True
                break

            if has_dependents:
                raise self.HasDependents('Object %s has dependents and cannot be deleted.' % repr(self))

        # Sends a signal call before to delete
        pre_delete.send(instance=self, sender=self.__class__)

        # Sends a signal call for deletion (to database engines)
        ret = model_delete.send(instance=self)

        # Sends a signal call after deletion
        post_delete.send(instance=self, sender=self.__class__)

        # Sets itself as deleted
        self._deleted = True

    def validate_before_save(self):
        """This method is responsible for new values validation before saving."""
        def unique_validation(fields, values):
            filters = dict(zip(fields, values))
            qs = self.query().filter(**filters)
            if self['pk']:
                qs = qs.exclude(pk=self['pk'])
            if qs.count():
                raise DuplicatedUniqueIndex('Another object with field(s) %s equal to %s already exist.'%(
                    ', '.join(fields), ', '.join(map(repr, values))))

        # Validations by field
        for field_name, value in self._new_values.items():
            if field_name not in self._meta.fields: continue

            field = self._meta.fields[field_name]

            # Unique index fields
            if field.unique:
                unique_validation([field_name], [value])

        # Unique together indexes
        for fields in self._meta.unique_together:
            unique_validation(fields, [self[f] for f in fields])

class BaseModelMetaclass(type):
    meta_base_class = ModelMeta

    def __new__(cls, name, bases, attrs):
        fields = []
        module = attrs.get('__module__','unknown')

        # Inherited field attributes
        if issubclass(bases[0], BaseModel) and hasattr(bases[0], '_meta') and bases[0]._meta.abstract:
            fields.extend(bases[0]._meta.fields.items())

        # Sorted field attributes
        if bases[0] not in (BaseModel, PersistentModel):
            for attr, obj in attrs.items():
                if not isinstance(obj, Field): continue
                obj.name = attr
                fields.append((attr, attrs.pop(attr)))
            fields.sort(key=lambda x: x[1].creation_counter)
            fields = SortedDict(fields)

        new_class = super(BaseModelMetaclass, cls).__new__(cls, name, bases, attrs)

        if bases[0] not in (BaseModel, PersistentModel):
            new_class._meta = cls.meta_base_class(new_class)
            new_class._meta.fields = fields

            # How new fields contribute to class
            for field in fields.values():
                if hasattr(field, 'contribute_to_class'):
                    field.contribute_to_class(new_class)

            app_label, model_label = new_class._meta.app_label, new_class._meta.model_label
            new_class._meta.path_label = '%s.%s'%(app_label, model_label)
            _registered_models[new_class._meta.path_label] = new_class

        new_class.DoesNotExist = type(name+'DoesNotExist', (ObjectDoesNotExist,), {'__module__':module})
        new_class.MultipleReturned = type(name+'MultipleReturned', (MultipleObjectsReturned,), {'__module__':module})
        new_class.HasDependents = type(name+'HasDependents', (ObjectHasDependents,), {'__module__':module})

        return new_class


# PERSISTENT MODELS

class ModelMetaclass(BaseModelMetaclass):
    pass

class Model(PersistentModel):
    __metaclass__ = ModelMetaclass


# NESTED MODELS

class NestedModelMetaclass(BaseModelMetaclass):
    pass

class NestedModel(BaseModel):
    __metaclass__ = NestedModelMetaclass



