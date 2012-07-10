import datetime
import decimal

try:
    import json as simplejson
except ImportError:
    import simplejson

from london.utils.functional import Promise
from london.utils.datatypes import Money
from london.utils.formats import sanitize_separators

class CustomJSONEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj) if obj else None
        elif isinstance(obj, Money):
            return float(sanitize_separators(str(obj))) if obj else None
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S') if obj else None
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d') if obj else None
        elif isinstance(obj, datetime.time):
            return obj.strftime('%H:%M:%S') if obj else None
        elif obj.__class__.__name__ == 'ObjectId':
            return str(obj)
        elif callable(obj):
            obj = obj()
            if isinstance(obj, Promise):
                obj = unicode(obj)
            return obj
        return super(CustomJSONEncoder, self).default(obj)

class CustomJSONDecoder(simplejson.JSONDecoder):
    pass

