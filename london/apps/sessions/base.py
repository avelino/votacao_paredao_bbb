from london.apps.sessions import app_settings
from london.utils.imports import import_anything

class BaseSession(object):
    key = None
    modified = False
    _values = None

    def __init__(self, key=None, request=None):
        self.key = key
        self.request = request
        self._values = {}

        if self.key:
            self.load()
        else:
            self.create()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._values[key] = value
        self.modified = True

    def __delitem__(self, key):
        del self._values[key]
        self.modified = True

    def get(self, key, default=None):
        return self._values.get(key, default)

    def set(self, key, value):
        self[key] = value

    def setdefault(self, key, value):
        return self._values.setdefault(key, value)

    def delete(self, key):
        del self[key]

    def create(self):
        raise NotImplementedError('Method "create" not implemented')

    def load(self):
        raise NotImplementedError('Method "load" not implemented')

    def save(self):
        raise NotImplementedError('Method "save" not implemented')

    def items(self):
        return self._values.items()

    def keys(self):
        return [k for k,v in self._values.items()]

    def update(self, other_session):
        for key, value in other_session.items():
            self[key] = value

def get_session_class():
    return import_anything(app_settings.STORE_CLASS)

