import hashlib

from london.db.signals import model_list, model_list_delete, model_list_count, model_list_update
from london.db.signals import manytomany_model_append, manytomany_model_remove
from london.db.signals import nested_model_append, nested_model_remove
from london.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from london.db.utils import get_related_class
from london.utils.imports import import_anything

class BaseQuerySet(object):
    def has_changed(self):
        return False

    def make_hash(self):
        items_hashs = [item.make_hash() if hasattr(item, 'make_hash') else str(item) for item in self]
        return hashlib.sha1('\n'.join(items_hashs)).hexdigest()

    def defer(self, *fields):
        raise NotImplementedError()

    def only(self, *fields):
        raise NotImplementedError()

    def values_list(self, *fields, **kwargs):
        flat = kwargs.get('flat', False)
        items = []

        fields = fields or self.model._meta.fields.keys()

        for obj in self.only(*fields):
            items.append(tuple([obj[f] for f in fields]))

        if flat:
            if len(fields) != 1:
                raise ValueError('Method .values_list() with flatten results supports just 1 field.')

            items = [item[0] for item in items]

        return tuple(items)

class QuerySet(BaseQuerySet):
    model = None
    _cached_results = None
    _chained_actions = None # Responsible to store filters, excludes, distincts, etc.
    _empty_results = False
    
    def __init__(self, model=None):
        self.model = model or self.model
        self._chained_actions = []

    def __iter__(self):
        if self._cached_results is None:
            self._cached_results = self._execute()

        for cursor in self._cached_results:
            for item in cursor:
                item['_origin'] = getattr(self._cached_results, '_origin', None)
                obj = self.model(_set_old_values=True, **item)
                yield obj

    def __len__(self): # This makes two requests, one for count() and other for the usual data retrieving
        return self.count()

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            self._chained_actions.append(('skip', idx.start))
            self._chained_actions.append(('limit', idx.stop))
            return list(self)
        elif isinstance(idx, int):
            self._chained_actions.append(('skip', idx))
            self._chained_actions.append(('limit', 1))
            return list(self)[0]
        return list(self)[idx]

    def _execute(self):
        if self._empty_results:
            return []
        else:
            return model_list.send(query=self)

    def _clone(self):
        clone = self.__class__(model = self.model)
        clone._chained_actions = list(self._chained_actions)
        return clone

    def __deepcopy__(self, memo):
        return self._clone()

    def get_flatten_actions(self):
        filter_if_all = {}
        actions = []
        has_ordering = False

        # Loops on chained actions to bound them up
        for action in self._chained_actions:
            if action[0] == 'filter_if_all':
                filter_if_all.update(action[1])
            else:
                actions.append(action)

            has_ordering = has_ordering or action[0] == 'order_by'

        # Appends filter_if_all action as one
        if filter_if_all:
            actions.insert(0, ('filter_if_all', filter_if_all))

        # Default ordering from Meta class attribute "ordering"
        if not has_ordering and getattr(self.model._meta, 'ordering', None):
            actions.append(('order_by', self.model._meta.ordering))

        return actions

    def get(self, **filters):
        """
        Returns just an object matching to the given arguments. If not found, an exception CLASS.DoesNotExist
        is raised, if more than one object are found, an exception CLASS.MultipleReturnedObjects is raised.
        """
        clone = self._clone()
        clone._chained_actions.append(('filter_if_all', filters))
        results = filter(bool, clone._execute())
        if results:
            results = reduce(lambda a,b: a+b, results)

        if not results:
            raise self.model.DoesNotExist('%s was not found for filters %s'%(self.model.__name__, filters))
        elif len(results) > 1:
            raise MultipleObjectsReturned('Many %s objects was found for filters %s'%(self.model.__name__, filters))

        values = results[0] or {}

        return self.model(_set_old_values=True, **values)

    def get_or_create(self, defaults=None, _ignore_multiple=False, **filters):
        """
        Returns the object and a boolean value about if this is a new object (was created right now)
        """
        try:
            if _ignore_multiple:
                return self.filter(**filters)[0], False
            else:
                return self.get(**filters), False
        except (self.model.DoesNotExist, IndexError):
            values = filters
            if defaults:
                values.update(defaults)
            return self.create(**values), True

    def create_or_update(self, values=None, defaults=None, **filters):
        if values:
            defaults = defaults or {}
            defaults.update(values)

        obj, new = self.get_or_create(defaults=defaults, **filters)

        if not new and values:
            for k,v in values.items():
                obj[k] = v
            obj.save()

        return obj, new

    def create(self, **values):
        return self.model(_save=True, **values)

    def filter(self, **kwargs):
        return self.filter_if_all(**kwargs)

    def first(self, *fields):
        fields = fields or self.model._meta.ordering

        if not fields:
            raise TypeError('For method .latest() the meta "ordering" or a fields list must have a field name.')

        try:
            return self.order_by(*fields)[0]
        except IndexError:
            raise self.model.DoesNotExist()

    def latest(self, *fields):
        fields = fields or self.model._meta.ordering

        if not fields:
            raise TypeError('For method .latest() the meta "ordering" or a fields list must have a field name.')

        fields = [('' if f.startswith('-') else '-') + f for f in fields]

        try:
            return self.order_by(*fields)[0]
        except IndexError:
            raise self.model.DoesNotExist()

    def filter_if_all(self, **kwargs):
        """Filters as an AND operation, that means all of keys and values given must be True to be in the filter."""
        clone = self._clone()
        clone._chained_actions.append(('filter_if_all', kwargs))
        return clone

    def filter_if_any(self, *args, **kwargs):
        """Acts as an OR condition, where all the filter keys are put in an OR clause, that means ANY of them
        can be True to get it in the filter.

        Arguments should be dictionaries with composite criteria, like:

        ...filter_if_any(dict(key='123', passengers=4), dict(key='321', passengers=3))

        it's like:

        ... WHERE (key='123' AND passengers=4) OR (key='321' AND passengers=3)
        """
        criteria = list(args) + [{k:v} for k,v in kwargs.items()]
        clone = self._clone()
        clone._chained_actions.append(('filter_if_any', criteria))
        return clone

    def exclude(self, **kwargs):
        return self.exclude_if_all(**kwargs)

    def exclude_if_all(self, **kwargs):
        """Excludes by an AND operation, that means all of keys and values given must be True to be excluded from
        the results."""
        clone = self._clone()
        clone._chained_actions.append(('exclude_if_all', kwargs))
        return clone

    def exclude_if_any(self, **kwargs):
        """Acts as an OR condition, where all the exclusion keys are put in an OR clause, that means ANY of them
        can be True to get it in the excluding."""
        clone = self._clone()
        clone._chained_actions.append(('exclude_if_any', kwargs))
        return clone

    def delete(self, force_if_has_dependents=False):
        model_list_delete.send(query=self, force_if_has_dependents=force_if_has_dependents)
        
    def update(self, **kwargs):
        model_list_update.send(query=self, items=kwargs)

    def count(self):
        return sum(model_list_count.send(query=self))

    def defer(self, *fields):
        clone = self._clone()
        clone._chained_actions.append(('defer', fields))
        return clone

    def only(self, *fields):
        clone = self._clone()
        clone._chained_actions.append(('only', fields))
        return clone

    def values(self, *fields):
        items = []
        fields = fields or self.model._meta.fields.keys()

        for obj in self.only(*fields):
            items.append(dict([(f, obj[f]) for f in fields]))

        return tuple(items)

    def order_by(self, *fields):
        clone = self._clone()
        clone._chained_actions.append(('order_by', fields))
        return clone

    def aggregate(self, **fields):
        # TODO
        return dict([(k,None) for k in fields.keys()]) # FIXME

    def group_by(self, *fields):
        # TODO
        clone = self._clone()
        clone._chained_actions.append(('group_by', fields))
        return clone

    def empty(self):
        clone = self._clone()
        clone._empty_results = True
        return clone

class RelatedQuerySet(object):
    _instance = None

    def __init__(self, model, related_field_name):
        super(RelatedQuerySet, self).__init__(model)
        self.related_field_name = related_field_name

    def set_instance(self, instance):
        self._instance = instance
        self._chained_actions.append(('filter_if_all', {self.related_field_name: self._instance}))

    def create(self, **values):
        if self._instance:
            values[self.related_field_name] = self._instance
        return super(RelatedQuerySet, self).create(**values)

    def _clone(self):
        clone = self.__class__(self.model, self.related_field_name)
        clone._chained_actions = list(self._chained_actions) # This is bugged FIXME
        clone._instance = self._instance
        return clone


def make_related_queryset(model, related_field_name):
    """
    Factory method to make a queryset class based on the model queryset and the RelatedQuerySet, so it
    gets a new instance to return. This is important to return a queryset with all model's queryset methods
    and the RelatedQuerySet methods as well.
    """
    model_queryset_class = import_anything(model._meta.query)
    new_class = type('%s%sRelatedQuerySet'%(model.__name__, related_field_name), (RelatedQuerySet, model_queryset_class), {})
    return new_class(model, related_field_name)


class ManyToManyRelatedQuerySet(object):
    _instance = None

    def __init__(self, model, related_field_name):
        super(ManyToManyRelatedQuerySet, self).__init__(model)
        self.related_field_name = related_field_name

    def set_instance(self, instance):
        self._instance = instance
        self._chained_actions.append(('filter_if_all', {self.related_field_name: self._instance['pk']}))

    def _clone(self):
        clone = self.__class__(self.model, self.related_field_name)
        clone._chained_actions = list(self._chained_actions) # This is bugged FIXME
        clone._instance = self._instance
        return clone


def make_m2m_related_queryset(model, related_field_name):
    """
    Factory method to make a queryset class based on the model queryset and the ManyToManyRelatedQuerySet, so it
    gets a new instance to return. This is important to return a queryset with all model's queryset methods
    and the ManyToManyRelatedQuerySet methods as well.
    """
    model_queryset_class = import_anything(model._meta.query)
    new_class = type('%s%sRelatedQuerySet'%(model.__name__, related_field_name), (ManyToManyRelatedQuerySet, model_queryset_class), {})
    return new_class(model, related_field_name)


class MemoryQuerySet(BaseQuerySet):
    _items = None

    def __init__(self, items=None):
        self._items = items if items is not None else []

    def __iter__(self):
        for item in self._items:
            yield item

    def append(self, obj, new=True):
        self._items.append(obj)

    def remove(self, index):
        self._items.remove(index)

    def order_by(self, *fields):
        def sort(a,b):
            for name in fields:
                comp = cmp(a[name.replace('-','')], b[name.replace('-','')])
                if name.startswith('-'):
                    comp = comp * -1
                if comp:
                    return comp
            return 0
        items = list(self._items)
        items.sort(sort)
        return items

    def count(self):
        return len(self._items)


class BaseChildQuerySet(BaseQuerySet):
    parent = None
    field = None
    related_class = None
    _items = None

    def __init__(self, items, parent, field):
        self.parent = parent
        self.field = field
        self.related_class = get_related_class(field, parent) if field.related else None
        self._items = []

        for item in (items or []):
            self.append(item, new=False)

        self._old_hash = self.make_hash()

    def __iter__(self):
        for item in self._items:
            yield item

    def __getitem__(self, idx):
        return self._items[idx]

    def append(self, obj, new=True):
        if self.related_class:
            if isinstance(obj, dict):
                obj = self.related_class(_nested_into=self.parent, **obj)
            elif not isinstance(obj, self.related_class):
                cls_name = '%s.%s'%(self.related_class.__module__, self.related_class.__name__)
                raise TypeError('Invalid object type "%s". Must be an instance from "%s"'%(repr(obj.__class__), cls_name))
        else:
            if isinstance(obj, dict):
                obj = import_anything(items['_class'])(_nested_into=self.parent, **obj)

        self._items.append(obj)
        return obj

    def remove(self, index_or_object):
        if index_or_object in self._items:
            obj = index_or_object
        else:
            obj = self._items[index]
        self._items.remove(obj)

    def delete(self):
        self._items = []

    def has_changed(self):
        return self._old_hash != self.make_hash()

    def only(self, *fields):
        for item in self:
            yield dict([(field,item[field]) for field in fields])

    def get(self, **kwargs):
        found = []
        for item in self._items:
            match = True
            for k,v in kwargs.items():
                if item[k] != v:
                    match = False
                    break
            if match:
                found.append(item)

        if not found:
            raise ObjectDoesNotExist()
        elif len(found) > 1:
            raise MultipleObjectsReturned()

        return found[0]


class ManyToManyQuerySet(BaseChildQuerySet):
    def append(self, obj, new=True):
        object_pk = None
        if isinstance(obj, self.related_class):
            object_pk = obj['pk']
        else:
            object_pk = obj
            try:
                inst = self.related_class.query().get(pk=object_pk)
                obj = inst
            except self.related_class.DoesNotExist:
                pass

        if object_pk not in self._items:
            self._items.append(object_pk)
            manytomany_model_append.send(instance=obj, queryset=self, new=new, sender=self.related_class)

        return obj

    def remove(self, index):
        obj = self[index]
        super(ManyToManyQuerySet, self).remove(index)
        manytomany_model_remove.send(instance=obj, queryset=self, sender=self.related_class)

    def __getattr__(self, name):
        # This makes it proxy the internal queryset
        return getattr(self._related_queryset(), name)

    def __str__(self):
        return str(self._related_queryset())

    def __iter__(self):
        for item in self._related_queryset():
            yield item

    def __getitem__(self, idx):
        return self._related_queryset()[idx]

    def _related_queryset(self):
        return self.related_class.query().filter(pk__in=self._items)


class NestedQuerySet(BaseChildQuerySet):
    def append(self, obj, new=True):
        obj = super(NestedQuerySet, self).append(obj, new)
        obj._nested_into = self.parent
        nested_model_append.send(instance=obj, queryset=self, new=new, sender=self.related_class)

    def remove(self, index):
        super(NestedQuerySet, self).remove(index)
        nested_model_remove.send(instance=obj, queryset=self, sender=self.related_class)

    def order_by(self, *fields):
        def sort(a,b):
            for name in fields:
                comp = cmp(a[name.replace('-','')], b[name.replace('-','')])
                if name.startswith('-'):
                    comp = comp * -1
                if comp:
                    return comp
            return 0
        items = list(self._items)
        items.sort(sort)
        return items

    def count(self):
        return len(self._items)

