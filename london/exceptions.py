class ApplicationNotFound(BaseException): pass

class URLNotFound(BaseException): pass
class NoReverseMatch(BaseException): pass
class TemplateNotFound(BaseException): pass
class IgnoreField(BaseException): pass
class ImproperlyConfigured(BaseException): pass

class ObjectDoesNotExist(BaseException): pass
class ObjectHasDependents(BaseException): pass
class MultipleObjectsReturned(BaseException): pass
class InvalidRelationValue(BaseException): pass
class ModelClassNotFound(BaseException): pass
class InvalidQueryClause(BaseException): pass
class DuplicatedUniqueIndex(BaseException): pass
class FieldDoesNotExist(BaseException): pass

class SuspiciousOperation(BaseException): pass
class ConnectionClosed(BaseException): pass

class ValidationError(BaseException):
    """Validation exception used by models and forms."""
    field_name = None

    def __init__(self, *args, **kwargs):
        if 'field_name' in kwargs:
            self.field_name = kwargs.pop('field_name')
        super(ValidationError, self).__init__(*args, **kwargs)

