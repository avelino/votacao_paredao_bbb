from london.db.engines.base import DatabaseEngine
from london.db.signals import model_save, model_delete, model_list
from london.db.signals import model_get_pk, model_list_delete, model_list_count, model_list_update

def force_unicode(value, errors='replace'):
    return value

def filter_item(filters):
    def _inner(obj):
        for k,v in filters.items():
            if k == '$nor':
                for condition_set in v:
                    cond = []
                    for k2,v2 in condition_set.items():
                        cond.append(obj.has_key(k2) and obj.get(k2, None) == v2)
                    if all(cond):
                        return False
            elif k == '$or':
                cond = []
                for condition_set in v:
                    cond2 = True
                    for k2,v2 in condition_set.items():
                        if not obj.has_key(k2) or obj.get(k2, None) != v2:
                            cond2 = False
                            break
                    cond.append(cond2)
                if not any(cond):
                    return False
            elif not obj.has_key(k) or obj.get(k, None) != v:
                return False
        return True
    return _inner

class MemoryEngine(DatabaseEngine):
    _objects = None
    
    def __init__(self, host=None, port=None, name=None, **kwargs):
        self.host = host if host is not None else self.host
        self.port = port if port is not None else self.port
        self.name = name if name is not None else self.name
        self.options = kwargs

        # Dipatcher connections
        model_list.connect(self.execute_query)
        model_save.connect(self.save_object)
        model_get_pk.connect(self.get_object_pk)
        model_delete.connect(self.delete_object)
        model_list_delete.connect(self.delete_list)
        model_list_count.connect(self.get_list_count)
        model_list_update.connect(self.update_list)

    def is_open(self):
        return True

    def open(self):
        if self._objects is not None: return

        self._objects = {}

    def get_object_pk(self, instance):
        return instance.get('_id', None)

    def execute_query(self, query, **kwargs):
        self.open()
        find_criteria, order_by, skip, limit = self._make_criteria(query)
        objects = filter(lambda a: a['_class'] == query.model, self._objects.values())
        results = filter(filter_item(find_criteria), objects)
        return results

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

    def clean_values(self, values):
        def clean_value(key, value):
            if isinstance(value, basestring) and not isinstance(value, unicode):
                return key, force_unicode(value, errors='replace')
            else:
                return key, value

        return dict([clean_value(key, value) for key,value in values.items()])

    def save_object(self, instance):
        cleaned_values = self.clean_values(instance._new_values)
        cleaned_values['_class'] = instance.__class__

        if instance['_id']:
            self._objects[instance['_id']].update(cleaned_values)
        else:
            max_pk = max(self._objects.keys()) if self._objects else 0
            cleaned_values['pk'] = instance['pk'] = cleaned_values['_id'] = instance['_id'] = max_pk + 1
            self._objects[cleaned_values['_id']] = cleaned_values

    def delete_object(self, instance):
        self.open()
        del self._objects[instance['pk']]

    def delete_list(self, query):
        self.open()
        find_criteria, order_by, skip, limit = self._make_criteria(query)
        objects = filter(lambda a: a['_class'] == query.model, self._objects.values())
        results = filter(filter_item(find_criteria), objects)
        self._objects = dict([(k,v) for k,v in self._objects.items() if v not in results])

    def update_list(self, query, items):
        self.open()
        find_criteria, order_by, skip, limit = self._make_criteria(query)
        objects = filter(lambda a: a['_class'] == query.model, self._objects.values())
        results = filter(filter_item(find_criteria), objects)
        for obj in results:
            for k,v in items.items():
                obj[k] = v

    def get_list_count(self, query):
        self.open()
        find_criteria, order_by, skip, limit = self._make_criteria(query)
        objects = filter(lambda a: a['_class'] == query.model, self._objects.values())
        return len(filter(filter_item(find_criteria), objects))

    def _clean_filters(self, filters):
        return filters

