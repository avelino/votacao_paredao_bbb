# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from london.db import _registered_models
from london.db.models.querysets import MemoryQuerySet
from london.db.models.fields import ForeignKey
from london.db.engines.base import DatabaseEngine
from london.db.signals import db_post_open, model_save, model_delete, model_get_pk, model_clear_pk
from london.db.signals import model_list, model_list_count, model_list_delete, model_list_update
from london.db.signals import model_set_dependent, model_unset_dependent, model_get_dependents, model_register_dependents
from london.utils.crypting import EncryptedString
from london.utils.encoding import force_unicode
from london.exceptions import ModelClassNotFound, ObjectDoesNotExist
from london.core.files.uploadedfile import UploadedFile
from london.utils.datatypes import Money

try:
    import pymongo # pymongo==2.0
    from bson.dbref import DBRef
except ImportError:
    pymongo = None
    DBRef = None

try:
    from pymongo.objectid import ObjectId, InvalidId
except ImportError:
    try:
        from bson.objectid import ObjectId
        from bson.errors import InvalidId
    except ImportError:
        ObjectId = InvalidId = None

class MongoDB(DatabaseEngine):
    host = 'localhost'
    port = 27017
    name = None
    options = None
    _connection = None

    def __init__(self, host=None, port=None, name=None, **kwargs):
        self.host = host if host is not None else self.host
        self.port = port if port is not None else self.port
        self.name = name if name is not None else self.name
        self.options = kwargs

        # Dipatcher connections
        model_list.connect(self.execute_query)
        model_save.connect(self.save_object)
        model_get_pk.connect(self.get_object_pk)
        model_clear_pk.connect(self.clear_object_pk)
        model_delete.connect(self.delete_object)
        model_list_delete.connect(self.delete_list)
        model_list_count.connect(self.count_list)
        model_list_update.connect(self.update_list)
        model_set_dependent.connect(self.set_dependent)
        model_unset_dependent.connect(self.unset_dependent)
        model_get_dependents.connect(self.get_dependents)
        model_register_dependents.connect(self.register_dependents)

    def is_open(self):
        return bool(self._connection)

    def open(self):
        if self._connection: return

        # Supporting replica sets
        if self.options.get('replicaSet', None):
            self._connection = pymongo.ReplicaSetConnection('%s:%s'%(self.host, self.port), replicaSet=self.options['replicaSet'])
        else:
            self._connection = pymongo.Connection(host=self.host, port=self.port)

        self.prepare_indexes()
        db_post_open.send(connection=self)

    def get_collection(self, name):
        self.open()
        return self._connection[self.name][name]

    def get_model_class_for_collection(self, name):
        for cls in _registered_models.values():
            if cls._meta.db_storage == name:
                return cls
        raise ModelClassNotFound('Model class for collection "%s" not found.'%name)

    def get_object_pk(self, instance):
        # TODO: this code should return something only if the instance comes from this database connection
        return instance['_id']

    def clear_object_pk(self, instance):
        # TODO: this code should work only if the instance comes from this database connection
        instance['_id'] = None

    def _make_criteria(self, query):
        actions = query.get_flatten_actions()
        find_criteria = {}
        order_by = []
        limit = None
        skip = None
        for action in actions:
            if action[0] == 'filter_if_all':
                find_criteria.update(self._clean_filters(action[1]))
            elif action[0] == 'filter_if_any' and action[1]:
                find_criteria.setdefault('$or', [])
                find_criteria['$or'].extend([self._clean_filters(c) for c in action[1]])
            elif action[0] == 'exclude_if_all':
                find_criteria.setdefault('$nor', [])
                find_criteria['$nor'].append(self._clean_filters(action[1]))
            elif action[0] == 'exclude_if_any':
                find_criteria.setdefault('$nor', [])
                find_criteria['$nor'].extend([{k:v} for k,v in self._clean_filters(action[1]).items()])
            elif action[0] == 'order_by':
                order_by.extend([(field.replace('-',''), -1 if field.startswith('-') else 1)
                    for field in action[1]])
            elif action[0] == 'skip':
                skip = action[1]
            elif action[0] == 'limit':
                limit = action[1]

        return find_criteria, order_by, skip, limit

    def execute_query(self, query, **kwargs):
        collection = self.get_collection(query.model._meta.db_storage)

        # Actions criteria
        find_criteria, order_by, skip, limit = self._make_criteria(query)

        # Supporting multiple database routing
        if not self.allow_read(query.model, **{'find_criteria':find_criteria, 'order_by':order_by, 'skip':skip, 'limit':limit}):
            return []

        # Basic results cursor with find criteria
        results = collection.find(find_criteria)

        # Sorting by fields from "order_by" method
        if order_by:
            results = results.sort(order_by)
        elif query.model._meta.ordering:
            results = results.sort([self.index_tuple(f) for f in query.model._meta.ordering])

        # Skip
        if skip:
            results = results.skip(skip)

        # Limit
        if limit:
            results = results.limit(limit)

        # Signs returned objects as coming through this connection
        results._origin = self.get_origin(query.model._meta.db_storage)

        if kwargs.get('return_cursor', False):
            return results

        return [self.clean_object_to_python(obj) for obj in results]

    def count_list(self, query, **kwargs):
        results = self.execute_query(query, return_cursor=True)
        return results.count(True) if results else 0

    def clean_values(self, values):
        return dict([self.clean_value(key, value) for key,value in values.items()])

    def clean_value(self, key, value):
        from london.db.models import PersistentModel, NestedQuerySet, ManyToManyQuerySet, QuerySet, RelatedQuerySet
        if key == '_id':
            return key, ObjectId(value)
        elif isinstance(value, (basestring, EncryptedString)) and not isinstance(value, unicode):
            return key, force_unicode(value, errors='replace')
        elif isinstance(value, (Decimal,Money)):
            return key, float(value)
        elif isinstance(value, PersistentModel):
            if value:
                value = {'_db_storage':value.__class__._meta.db_storage, 'pk':value['pk']}
            return key, value
        elif isinstance(value, NestedQuerySet):
            if value:
                value = [self.clean_values(item.get_values_to_save()) for item in value]
            return key, value
        elif isinstance(value, ManyToManyQuerySet):
            if value:
                value = [pk for pk in value._items] # FIXME bad code
            return key, value
        elif isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return key, datetime.datetime(value.year, value.month, value.day)
        elif isinstance(value, datetime.time):
            return key, value.strftime('%H:%M:%S')
        elif isinstance(value, (tuple, list, QuerySet, RelatedQuerySet)):
            return key, [self.clean_value(None, item)[1] for item in value]
        else:
            return key, value

    def save_object(self, instance):
        # Supporting multiple database routing
        if not self.allow_write(type(instance), 'save_object', instance=instance):
            return

        collection = self.get_collection(instance._meta.db_storage)
        cleaned_values = self.clean_values(instance.get_values_to_save())

        # Set ForeignKeys copying fields
        for name,value in cleaned_values.items():
            field = instance._meta.fields.get(name, None)
            original_value = instance[name]

            # Only valid value and ForeignKey fields
            if not value or not field or not isinstance(field, ForeignKey):
                continue

            # Only fields with copying_fields or copying_exclude
            if field.copying_fields:
                copying_fields = field.copying_fields
            elif field.copying_exclude:
                copying_fields = [n for n in original_value._meta.fields.key() if n not in field.copying_exclude]
            else:
                copying_fields = []

            # Setting coying fields to reference dictionary
            for copying_field in copying_fields:
                value[copying_field] = self.clean_value(copying_field, original_value[copying_field])[1]

        # Update
        if instance.pk:
            actions = {}
            if cleaned_values:
                actions['$set'] = cleaned_values
            if instance._deleted_values:
                actions['$unset'] = dict([(f,1) for f in instance._deleted_values])
    
            # Updates only if there is anything to update
            if actions:
                collection.update({'_id': instance['_id']}, actions)

        # Creation
        else:
            instance['_id'] = collection.insert(cleaned_values)

        self.register_dependents(instance, for_all=False)

    def clean_object_to_python(self, obj):
        for key, value in obj.items():
            if isinstance(value, DBRef) or (isinstance(value, dict) and '_db_storage' in value and 'pk' in value):
                ref = value.collection if isinstance(value, DBRef) else value['_db_storage']

                obj[key] = {}
                if isinstance(value, DBRef):
                    obj[key]['pk'] = value.id
                else:
                    obj[key].update(value)

                try:
                    obj[key]['class'] = self.get_model_class_for_collection(ref)
                except ModelClassNotFound:
                    obj[key]['_db_storage'] = ref

            elif isinstance(value, dict):
                obj[key] = self.clean_object_to_python(value)

            elif isinstance(value, list):
                obj[key] = [self.clean_object_to_python(i) if isinstance(i, dict) else i for i in value]
        return obj

    def get_origin(self, storage_name):
        return 'mongodb:%s.%s'%(self.name, storage_name)

    def delete_object(self, instance):
        # Supporting multiple database routing
        if not self.allow_write(type(instance), 'delete_object', instance=instance):
            return

        # Unlinking dependeds
        self.unlink_dependencies(instance)

        collection = self.get_collection(instance._meta.db_storage)
        return collection.remove({'_id': instance['_id']})

    def delete_list(self, query, force_if_has_dependents=False):
        # Supporting multiple database routing
        if not self.allow_write(query.model, 'delete_list', query=query):
            return

        collection = self.get_collection(query.model._meta.db_storage)
        find_criteria, order_by, skip, limit = self._make_criteria(query)

        # Ignores those objects with dependents
        if not force_if_has_dependents:
            for item in collection.find(find_criteria):
                meta = {
                    'dependent_db_storage': query.model._meta.db_storage,
                    'dependent_pk': item['_id'],
                    }
                if self.get_collection('london_dependents').find(meta).count():
                    raise query.model.HasDependents('Some of these objects have dependents.')

        # Unlinking dependeds
        for item in collection.find(find_criteria):
            self.unlink_dependencies(db_storage=query.model._meta.db_storage, pk=item['_id'])

        return collection.remove(find_criteria)

    def update_list(self, query, items):
        # Supporting multiple database routing
        if not self.allow_write(query.model, 'update_list', query=query):
            return

        collection = self.get_collection(query.model._meta.db_storage)
        find_criteria, order_by, skip, limit = self._make_criteria(query)

        # Updates only if there is anything to update
        if items:
            return collection.update(find_criteria, {'$set': self.clean_values(items)}, multi=True)

    def _clean_filters(self, filters):
        if filters and 'pk' in filters:
            try:
                filters['_id'] = ObjectId(filters.pop('pk'))
            except InvalidId:
                #raise TypeError('Invalid primary key.')
                pass
        
        # Applies the filter lookups
        new_filters = {}
        if isinstance(filters, dict):
            filters = self.clean_values(filters)
            for key, value in filters.items():
                key_bits = key.split('__')
                new_key, value = self._clean_filter_value(key_bits, value)

                # Converting a persistent model dict
                if isinstance(value, dict) and 'pk' in value and '_db_storage' in value:
                    new_filters['%s.pk'%key] = value['pk']
                    new_filters['%s._db_storage'%key] = value['_db_storage']

                elif isinstance(value, dict) and isinstance(new_filters.get(new_key, {}), dict):
                    new_filters.setdefault(new_key, {})
                    new_filters[new_key].update(value)
                else:
                    new_filters[new_key] = value

        return new_filters

    def _clean_filter_value(self, key_bits, value):
        if key_bits[0] == 'pk':
            if isinstance(value, basestring):
                value = ObjectId(value)
            elif isinstance(value, (tuple, list)):
                value = [ObjectId(v) for v in value]

        # Treats field lookups
        ret = {}
        if 'contains' in key_bits:
            ret['$regex'] = '%s'%value
            ret['$options'] = 'm'
            key_bits.remove('contains')
        if 'icontains' in key_bits:
            ret['$regex'] = '%s'%value
            ret['$options'] = 'i'
            key_bits.remove('icontains')
        if 'startswith' in key_bits:
            ret['$regex'] = '^%s'%value
            ret['$options'] = 'm'
            key_bits.remove('startswith')
        if 'istartswith' in key_bits:
            ret['$regex'] = '^%s'%value
            ret['$options'] = 'i'
            key_bits.remove('istartswith')
        if 'endswith' in key_bits:
            ret['$regex'] = '%s$'%value
            ret['$options'] = 'm'
            key_bits.remove('endswith')
        if 'iendswith' in key_bits:
            ret['$regex'] = '%s$'%value
            ret['$options'] = 'i'
            key_bits.remove('iendswith')
        if 'gt' in key_bits:
            ret['$gt'] = value
            key_bits.remove('gt')
        if 'gte' in key_bits:
            ret['$gte'] = value
            key_bits.remove('gte')
        if 'lt' in key_bits:
            ret['$lt'] = value
            key_bits.remove('lt')
        if 'lte' in key_bits:
            ret['$lte'] = value
            key_bits.remove('lte')
        if 'in' in key_bits:
            ret['$in'] = value
            key_bits.remove('in')
        if 'notin' in key_bits:
            ret['$nin'] = value
            key_bits.remove('notin')
        if 'exists' in key_bits:
            ret['$exists'] = bool(value)
            key_bits.remove('exists')
        if 'notequal' in key_bits:
            ret['$ne'] = value
            key_bits.remove('notequal')
        if 'length' in key_bits:
            ret['$size'] = value
            key_bits.remove('length')
        if 'regex' in key_bits:
            ret['$regex'] = value
            ret['$options'] = 'm'
            key_bits.remove('regex')
        if 'iregex' in key_bits:
            ret['$regex'] = value
            ret['$options'] = 'i'
            key_bits.remove('iregex')
        if 'isnull' in key_bits:
            if value:
                ret['$in'] = [None]
            else:
                ret['$ne'] = None
            key_bits.remove('isnull')
        if 'year' in key_bits:
            ret['$gte'] = datetime.date(value,1,1)
            ret['$lt'] = datetime.date(value,12,31)
            key_bits.remove('year')

        new_key = '.'.join(key_bits)
        new_key = '_id' if new_key == 'pk' else new_key

        return new_key, ret or value

    def index_tuple(self, name):
        ret = (name.replace('-',''), pymongo.ASCENDING if name.startswith('-') else pymongo.DESCENDING)
        return ret

    def index_name(self, name):
        ret = name.replace('-','d_')
        return ret

    def ensure_index(self, collection, name, fields, unique=False):
        info = collection.index_information()
        name = self.index_name(name)
        if name not in info:
            collection.ensure_index(fields, name, unique=unique)
            info[name] = fields

    def prepare_indexes(self):
        """
        Checks all available model classes and their respective indexes and creates them.
        """
        for cls in _registered_models.values():
            # Supporting multiple database routing
            if not self.allow_prepare_indexes(cls):
                continue

            collection = self.get_collection(cls._meta.db_storage)
            # Fields from ordering entry
            if cls._meta.ordering:
                self.ensure_index(collection, '_'.join(cls._meta.ordering), [self.index_tuple(f) for f in cls._meta.ordering])

            # Fields with db_index=True
            for name, field in cls._meta.fields.items():
                if field.db_index and not field.unique:
                    self.ensure_index(collection, name, [self.index_tuple(name)])

            # Fields with unique=True
            for name, field in cls._meta.fields.items():
                if field.unique:
                    self.ensure_index(collection, name, [self.index_tuple(name)], unique=True)

            # Indexes
            for fields in (cls._meta.indexes or []):
                self.ensure_index(collection, '_'.join(fields), [self.index_tuple(f) for f in fields])

            # Unique together
            for fields in (cls._meta.unique_together or []):
                self.ensure_index(collection, '_'.join(fields), [self.index_tuple(f) for f in fields], unique=True)

    def create_database(self):
        self.open()

    def drop_database(self):
        self.open()
        self._connection.drop_database(self.name)

    # DEPENDENTS SIGNAL LISTENERS

    def set_dependent(self, dependent, depended, field):
        if not hasattr(dependent, '_mongodb_dependence_stack'):
            dependent._mongodb_dependence_stack = []
        dependent._mongodb_dependence_stack.append(('set', field, depended))

    def unset_dependent(self, dependent, depended, field):
        if not hasattr(dependent, '_mongodb_dependence_stack'):
            dependent._mongodb_dependence_stack = []
        dependent._mongodb_dependence_stack.append(('unset', field, depended))

    def get_dependents(self, instance):
        # Structure:
        #
        #   - dependent = instance
        #   - depended = the other
        #
        #   {'dependent_db_storage':, 'dependent_pk':, 'depended_db_storage':, 'depended_pk':}

        dependents = self.get_collection('london_dependents').find({
            'depended_db_storage': instance._meta.db_storage,
            'depended_pk': instance['pk'],
            })

        qs = MemoryQuerySet()

        for item in dependents:
            ref = item['dependent_db_storage']
            pk = item['dependent_pk']

            try:
                cls = self.get_model_class_for_collection(ref)
                obj = cls.query().get(pk=pk)
            except (ModelClassNotFound,ObjectDoesNotExist):
                obj = {'_db_storage':ref, 'pk':pk}

            qs.append(obj)

        return qs

    def register_dependents(self, instance, for_all=False):
        from london.db.models import PersistentModel, ManyToManyQuerySet, NestedQuerySet

        # Loads all fields containing a persistent model object as its value
        if for_all:
            stack = []
            for field_name,value in instance._old_values.items():
                field = instance._meta.fields.get(field_name, None)

                if not value:
                    continue

                # Ordinary persistent objects
                if (isinstance(value, PersistentModel) or value.__class__.__name__ == 'LazyLoadingObject'): # FIXME: this class name is a bad idea
                    stack.append(('set',field or field_name,value))

                # Persistent objects in a list field or many to many queryset
                elif isinstance(value, (list,ManyToManyQuerySet)):
                    for other in value:
                        stack.append(('set',field or field_name,other))

                # Persistent objects in a dict field
                elif isinstance(value, dict):
                    for other in value.values():
                        stack.append(('set',field or field_name,other))

                # Nested objects
                elif isinstance(value, NestedQuerySet):
                    for other in value:
                        for field_name2,value2 in other._old_values.items():
                            if (isinstance(value2, PersistentModel) or value2.__class__.__name__ == 'LazyLoadingObject'): # FIXME: this class name is a bad idea
                                stack.append(('set',field or field_name,other))

            stack = self.flatten_dependence_stack(instance, stack).values()

        else: # Just for those fields that were changed
            stack = self.flatten_dependence_stack(instance).values()

        # Gets a collection and prepares it with unique index
        dependents = self.get_collection('london_dependents')
        fields = [('dependent_db_storage',pymongo.ASCENDING), ('dependent_pk',pymongo.ASCENDING),
                ('depended_db_storage',pymongo.ASCENDING), ('depended_pk',pymongo.ASCENDING)]
        self.ensure_index(dependents, 'unique_dependents', fields, unique=True)

        # Sets dependents point back
        for action, field, depended in stack:
            if isinstance(depended, dict):
                continue

            meta = {
                'dependent_db_storage': instance._meta.db_storage,
                'dependent_pk': instance['pk'],
                'depended_db_storage': depended._meta.db_storage,
                'depended_pk': depended['pk'],
                }

            if action == 'set':
                dependents.insert(meta)
            elif action == 'unset':
                dependents.remove(meta)

    def flatten_dependence_stack(self, dependent, stack=None):
        from london.db.models import PersistentModel
        results = {}
        stack = stack or getattr(dependent, '_mongodb_dependence_stack', [])

        for action, field, depended in stack:
            # FIXME: This class name in string is not good, but otherwise we get circular reference here.
            if depended.__class__.__name__ == 'LazyLoadingObject' and isinstance(field, ForeignKey):
                depended = field.clean_value(dependent, depended.value)

                # Quits if related object wasn't found
                if not depended:
                    continue

            # Non persistent model objects are ignored
            if not isinstance(depended, PersistentModel):
                continue

            key = '%s:%s' % (field if isinstance(field, basestring) else field.name, depended['pk'])
            results[key] = (action, field, depended)
        return results


    def unlink_dependencies(self, instance=None, db_storage=None, pk=None):
        from london.db.models import PersistentModel

        if instance:
            keys = {
                'db_storage': instance._meta.db_storage,
                'pk': instance['pk'],
                }
        elif db_storage and pk:
            keys = {
                'db_storage': db_storage,
                'pk': pk,
                }
        else:
            raise TypeError('Invalid keys for dependencies unlinking.')

        # Instance's depended objects
        self.get_collection('london_dependents').remove({
            'depended_db_storage': keys['db_storage'],
            'depended_pk': keys['pk'],
            })

        # Objects depended by this instance
        self.get_collection('london_dependents').remove({
            'dependent_db_storage': keys['db_storage'],
            'dependent_pk': keys['pk'],
            })

