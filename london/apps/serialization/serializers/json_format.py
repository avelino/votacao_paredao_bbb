try:
    import json as simplejson
except ImportError:
    import simplejson

from london.apps.serialization.serializers.base import BaseSerializer, DeserializedObject
from london.db.models.querysets import QuerySet
from london.utils.json_encoding import CustomJSONEncoder, CustomJSONDecoder
from london.db.models import FileField

class JsonSerializer(BaseSerializer):
    extension = 'json'

    def serialize(self, obj):
        def make_dict(item):
            d = item.as_dict()

            # Setting file name to file fields
            for field in item._meta.fields.values():
                if isinstance(field, FileField):
                    d[field.name] = d[field.name].name

            # Meta information abou the object
            d['_model_class'] = '%s.%s'%(item._meta.app_label, item._meta.model_label)
            try:
                d['_natural_key'] = item.get_natural_key()
            except AttributeError:
                d['_natural_key'] = {'pk':item['pk']}

            return d

        if isinstance(obj, (list, tuple, QuerySet)):
            objects = [make_dict(o) for o in obj]
        else:
            objects = [make_dict(obj)]

        return simplejson.dumps(objects, cls=CustomJSONEncoder)

    def deserialize(self, data):
        objects = simplejson.loads(data, cls=CustomJSONDecoder)
        return map(DeserializedObject, objects)

