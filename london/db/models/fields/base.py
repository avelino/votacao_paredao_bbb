"""
The class attribute "creation_counter" idea was partially copied from Django 1.4
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import datetime
from decimal import Decimal

from london.utils.crypting import EncryptedString
from london.utils.imports import import_anything
from london.conf import settings
from london.db.utils import get_related_class
from london.db.models.querysets import make_related_queryset, make_m2m_related_queryset, ManyToManyQuerySet, NestedQuerySet
from london.utils.slugs import slugify
from london.exceptions import InvalidRelationValue, MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from london.utils.datatypes import Money
from london.utils.safestring import mark_safe


class Field(object):
    name = None
    null = False
    blank = False
    default = None
    verbose_name = None
    base_type = 'undefined' # should be undefined, string, boolean, integer or float
    choices = None
    db_index = False
    unique = False
    help_text = ''
    is_file_field = False
    auto = None
    lazy_load = False

    # This class attribute increments each time a field is created to keep the right field order
    creation_counter = 0

    def __init__(self, **kwargs):
        self.null = kwargs.get('null', self.null)
        self.blank = kwargs.get('blank', self.blank)
        self.default = kwargs.get('default', self.default)
        self.verbose_name = kwargs.get('verbose_name', self.verbose_name)
        self.choices = kwargs.get('choices', self.choices)
        self.db_index = bool(kwargs.get('db_index', self.db_index))
        self.unique = bool(kwargs.get('unique', self.unique))
        self.help_text = kwargs.get('help_text', self.help_text)
        self.name = kwargs.get('name', self.name)
        self.auto = kwargs.get('auto', self.auto)

        # Increments creation counter to make possible to sort fields by creation order
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1        

    def clean_value(self, inst, value):
        """
        Used by other methods to clean and return the desirable Python format/data type.
        """
        return value

    def get_default(self, obj):
        """
        Returns the default value for this field. If default object is callable, then call
        it before to get the result as the default value (this is useful for datetime.now).
        """
        if callable(self.default):
            return self.default()
        else:
            return self.default

    def contribute_to_class(self, cls):
        """
        This function can be used to change the class logic, if necessary. Most of field types just don't
        anything.
        """
        if self.db_index:
            new_index = (self.name,)
            if new_index not in cls._meta.indexes:
                cls._meta.indexes = tuple(list(cls._meta.indexes) + [new_index])

    def contribute_to_object(self, obj):
        """
        This function does the same that "contribute_to_class" does, but for an object.
        """
        pass


class AnyField(Field):
    """
    Field to store any kind of value (an object has that field with an integer, another has
    a string, etc.)
    """
    pass


class CharField(Field):
    max_length = None
    base_type = 'string'
    force_lower_case = False
    force_upper_case = False
    force_capitalized = False

    def __init__(self, verbose_name=None, **kwargs):
        kwargs['verbose_name'] = verbose_name
        self.max_length = kwargs.pop('max_length', self.max_length)
        self.force_lower_case = kwargs.pop('force_lower_case', self.force_lower_case)
        self.force_upper_case = kwargs.pop('force_upper_case', self.force_upper_case)
        self.force_capitalized = kwargs.pop('force_capitalized', self.force_capitalized)

        if self.force_lower_case + self.force_upper_case + self.force_capitalized > 1:
            raise SyntaxError('A CharField can have only one of attributes "force_lower_case", "force_upper_case" and "force_capitalized" set as True.')

        super(CharField, self).__init__(**kwargs)

    def clean_value(self, inst, value):
        if isinstance(value, basestring) and value:
            if self.force_lower_case:
                value = value.lower()
            elif self.force_upper_case:
                value = value.upper()
            elif self.force_capitalized:
                value = value[0].upper() + value[1:]
        return value

    def get_default(self, inst):
        ret = super(CharField, self).get_default(inst)
        if ret is None and self.blank:
            return ''
        else:
            return ret


class TextField(Field):
    base_type = 'string'

    def __init__(self, **kwargs):
        kwargs.setdefault('blank', True)
        super(TextField, self).__init__(**kwargs)
            

class MarkdownField(Field):
    base_type = 'string'

    def __init__(self, **kwargs):
        kwargs.setdefault('blank', True)
        super(MarkdownField, self).__init__(**kwargs)
    
    def clean_value(self, inst, value):
        
        # Try to import markdonw2
        try:
            import markdown2
        except ImportError:
            markdown2 = None
            #raise ValidationError('Cannot import markdown2')
            
        if not isinstance(value, basestring):
            raise ValidationError('Invalid type. Expected string: %s'%value)
                    
        try:                
            value = markdown2.markdown(mark_safe(value))
        except:
            raise ValidationError('Error markdown: %s'%value)
        else:
            return value or ''
        

class EmailField(CharField):
    max_length = 100


class URLField(CharField):
    max_length = 200


class SlugField(CharField):
    max_length = 100

    def clean_value(self, inst, value):
        return slugify(value) if value else value


class PasswordField(CharField):
    max_length = 200
    algorithm = settings.DEFAULT_ENCRYPT_ALGORITHM # Could be sha256, sha512, md5, etc.

    def __init__(self, **kwargs):
        self.algorithm = kwargs.get('algorithm', self.algorithm)
        super(PasswordField, self).__init__(**kwargs)

    def clean_value(self, inst, value):
        if isinstance(value, EncryptedString) or value is None:
            return value
        else:
            return EncryptedString.make(value, self.algorithm)


class BooleanField(Field):
    base_type = 'boolean'

    def clean_value(self, inst, value):
        return bool(value)


class NullBooleanField(Field):
    base_type = 'boolean'

    def clean_value(self, inst, value):
        return bool(value) if value is not None else None


class IntegerField(Field):
    base_type = 'integer'

    def clean_value(self, inst, value):
        return int(value) if value is not None else None


class SmallIntegerField(IntegerField):
    base_type = 'integer'


class PositiveIntegerField(IntegerField):
    base_type = 'integer'


class PositiveSmallIntegerField(IntegerField):
    base_type = 'integer'


class DecimalField(Field):
    base_type = 'decimal'
    max_digits = None
    decimal_places = None

    def __init__(self, verbose_name=None, **kwargs):
        kwargs['verbose_name'] = verbose_name
        self.max_digits = kwargs.pop('max_digits', self.max_digits)
        self.decimal_places = kwargs.pop('decimal_places', self.decimal_places)
        super(DecimalField, self).__init__(**kwargs)

    def clean_value(self, inst, value):
        # If value is already Decimal
        if isinstance(value, Decimal) or value is None:
            return value
        # Converts to Decimal (string comes before to ensure integer and float numbers
        return Decimal(str(value))


class MoneyField(Field):
    base_type = 'decimal'

    def clean_value(self, inst, value):
        # If value is already Decimal
        if isinstance(value, Money) or value is None:
            return value

        # Converts to Decimal (string comes before to ensure integer and float numbers
        try:
            return Money(value)
        except (UnicodeEncodeError, ValueError):
            raise ValidationError('Invalid money value')


class DateField(Field):
    base_type = 'date'
    
    def clean_value(self, inst, value):
        if not value:
            return None
        elif isinstance(value, datetime.date):
            return value

        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return datetime.datetime.strptime(value, '%d/%m/%Y').date()


class DateTimeField(Field):
    base_type = 'datetime'
    
    def clean_value(self, inst, value):
        if not value:
            return None
        elif isinstance(value, datetime.datetime):
            return value
        elif isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)

        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    return datetime.datetime.strptime(value, '%d/%m/%Y %H:%M:%S').date()
                except ValueError:
                    try:
                        return datetime.datetime.strptime(value, '%d/%m/%Y %H:%M').date()
                    except ValueError:
                        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').date()


class TimeField(Field):
    base_type = 'time'
    
    def clean_value(self, inst, value):
        if isinstance(value, datetime.time) or value is None:
            return value

        try:
            return datetime.datetime.strptime(value, '%H:%M:%S').time()
        except ValueError:
            return datetime.datetime.strptime(value, '%H:%M').time()


class ListField(Field):
    base_type = 'list'


class DictField(Field):
    base_type = 'dict'


class WrongRelatedName(Exception): pass


class RelatedField(Field):
    def contribute_to_class(self, cls):
        """Adds the opposite attributes to this relation"""
        if not hasattr(cls, 'query'):
            return

        if self.related:
            # Transforms the "related" reference into a string like 'app.Model'
            if self.related == 'self':
                self.related = '%s.%s'%(cls._meta.app_label, cls._meta.model_label)
            elif isinstance(self.related, basestring) and '.' not in self.related:
                self.related = '%s.%s'%(cls._meta.app_label, self.related)
            elif not isinstance(self.related, basestring):
                self.related = self.related._meta.path_label

            self.related_name = self.make_related_name(cls, self.related_name)
            def bound_queryset(instance):
                return self.return_to_related(cls, instance)

            cls._meta.add_external_relation(self, cls, self.related_name, bound_queryset)

            # The old way didn't support recursive relations between different applications
            #related = get_related_class(self, cls)
            #related._meta.add_external_relation(self.related_name, bound_queryset)

    def make_related_name(self, cls, related_name):
        if not related_name:
            if self.related == '%s.%s'%(cls._meta.app_label, cls._meta.model_label):
                raise WrongRelatedName('Self reference requires a "related_name".')
            related_name = cls._meta.model_label.lower() + '_set'
        return related_name

    def return_to_related(self, cls, instance):
        qs = make_related_queryset(cls, self.name)._clone()
        qs.set_instance(instance)
        return qs


class ForeignKey(RelatedField):
    related = None
    related_name = None
    lazy_load = True
    copying_fields = None
    copying_exclude = None

    def __init__(self, related=None, **kwargs):
        self.related = related
        self.related_name = kwargs.get('related_name', self.related_name)
        self.copying_fields = kwargs.get('copying_fields', self.copying_fields)
        self.copying_exclude = kwargs.get('copying_exclude', self.copying_exclude)
        super(ForeignKey, self).__init__(**kwargs)

    def clean_value(self, inst, value):
        # TODO: supporting multiple database routing by the method "allow_relation"
        if isinstance(value, dict):
            if self.related:
                cls = get_related_class(self, inst)
            elif not value.get('class', None):
                raise InvalidRelationValue('The relation "%s" has not a class.'%value)
            else:
                if isinstance(value['class'], basestring):
                    try:
                        cls = import_anything(value['class'])
                    except ImportError:
                        raise InvalidRelationValue('The class for relation "%s" was not found.'%value)
                else:
                    cls = value['class']

            # Loads the related object
            try:
                value = cls.query().get(pk=value['pk'])
            except cls.DoesNotExist: # FIXME we have to find another way to treat this
                value['error'] = 'Object not found'
        return value

    def get_related_queryset(self, obj):
        if not self.related:
            return []

        return get_related_class(self, obj).query()


class OneToOneField(ForeignKey):
    def return_to_related(self, cls, instance):
        qs = super(OneToOneField, self).return_to_related(cls, instance)
        if qs.count() > 1:
            raise MultipleObjectsReturned('Many related objects for an OneToOneField.')
        elif qs.count() == 0:
            if self.null:
                return None
            else:
                raise cls.DoesNotExist('Object for OneToOneField was not found.')
        return qs[0]


class ManyToManyField(RelatedField):
    related = None
    related_name = None
    lazy_load = True

    def __init__(self, related, **kwargs):
        self.related = related
        self.related_name = kwargs.get('related_name', self.related_name)
        super(ManyToManyField, self).__init__(**kwargs)

    def get_default(self, inst):
        return ManyToManyQuerySet([], parent=inst, field=self)

    def clean_value(self, inst, value):
        if isinstance(value, ManyToManyQuerySet):
            value.parent = inst
            value.field = self
            return value
        else:
            return ManyToManyQuerySet(value, parent=inst, field=self)

    def get_related_queryset(self, obj):
        if not self.related:
            return []

        return get_related_class(self, obj).query()

    def return_to_related(self, cls, instance):
        qs = make_m2m_related_queryset(cls, self.name)._clone()
        qs.set_instance(instance)
        return qs


class NestedListField(Field):
    related = None

    def __init__(self, related=None, **kwargs):
        self.related = related
        super(NestedListField, self).__init__(**kwargs)

    def get_default(self, inst):
        return NestedQuerySet([], parent=inst, field=self)

    def clean_value(self, inst, value):
        if isinstance(value, NestedQuerySet):
            value.parent = inst
            value.field = self
            return value
        else:
            return NestedQuerySet(value, parent=inst, field=self)

