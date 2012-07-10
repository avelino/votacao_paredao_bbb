from london.db.utils import get_model

class BaseSerializer(object):
    extension = None

    def serialize(self, obj):
        pass

    def deserialize(self, data):
        pass

class DeserializedObject(object):
    def __init__(self, obj):
        self.model = get_model(obj.pop('_model_class'))
        self.natural_key = obj.pop('_natural_key')
        self._fields = obj
        
        try:
            if hasattr(self.model.query(), 'get_by_natural_key'):
                self.object = self.model.query().get_by_natural_key(**self.natural_key)
            else:
                self.object = self.model.query().get(**self.natural_key)
        except self.model.DoesNotExist:
            self.object = self.model()

        for k,v in self._fields.items():
            self.object[k] = v

    def save_object(self):
        self.object.save()

