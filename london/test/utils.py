"""
Utilities for test driven development. Originally written in django-plus
"""
import os, unittest, doctest
from london.db import models
from london.exceptions import FieldDoesNotExist

def assert_equal(*args):
    """Returns the arguments if any of them is different to the others, otherelse, returns empty."""
    for idx in range(len(args)-1):
        if args[idx] != args[idx+1]:
            print(u'\n<>\n'.join(map(unicode,args)))

def assert_not_equal(*args):
    """The opposite of assert_equal"""
    for idx in range(len(args)-1):
        if args[idx] == args[idx+1]:
            print(u'\n==\n'.join(map(unicode,args)))

def assert_equal_numbers(arg1, arg2):
    """Does the same of assert_equal but converts both to float to ensure they are in the same
    value type - as a number."""
    assert_equal(float(arg1), float(arg2))

def assert_contains(arg1, arg2):
    """Validates an item (arg2) in a list (arg1)"""
    if arg2 not in arg1:
        print('%s was not found in %s'%(arg2, arg1))

def assert_between(arg1, arg2, arg3):
    """Makes assertation, printing the values if the first is not greater or equal the second
    one and lower or equal to the third onde."""
    if arg1 < arg2 or arg1 > arg3:
        print('%s is not between %s and %s'%(arg1, arg2, arg3))

def assert_startswith(arg1, term):
    if not arg1.startswith(term):
        print("'%s' doesn't starts with '%s'"%(arg1, term))

def assert_endswith(arg1, term):
    if not arg1.endswith(term):
        print("'%s' doesn't starts with '%s'"%(arg1, term))

def assert_isinstance(inst, classes):
    if not isinstance(inst, classes):
        print("%s is not an instance of %s"%(inst, classes))

def assert_true(value):
    if not value:
        print(str(value) + " is not a True value")

def assert_false(value):
    if value:
        print("%s is not a False value"%value)

def model_has_fields(model_class, fields):
    """Checks if a model class has all fields in fields list and returns a
    list of fields that aren't in one of them.
    
    This method returns an empty list ( [] ) when everything is ok"""
    fields = set(fields)
    model_fields = set(model_class._meta.fields.keys())
    return list(fields - model_fields)

def is_field_type(model_class_from, field, field_type, **kwargs):
    """Checks if a field of a model class if of the type informed.
    If field_type value is a class, it compares just the class of field,
    if field_type is an instance of a field type class, it compares the
    max_length, max_digits and decimal_places, blank and null"""
    field = model_class_from._meta.fields[field]

    if field.__class__ != field_type:
        return False

    for k,v in kwargs.items():
        if k == 'to':
            if v != field.related:
                raise Exception('%s: %s'%(k, unicode(field.rel.to)))
        elif v != getattr(field, k, None):
            raise Exception('%s: %s'%(k, unicode(getattr(field, k, None))))

    return True

def is_model_class_fk(model_class_from, field, model_class_to):
    """Returns True if field is ForeignKey to model class informed"""
    try:
        model_field = model_class_from._meta.fields[field]
    except KeyError:
        raise FieldDoesNotExist('Model class "%s" has no declared field "%s"'%(model_class_from._meta.path_label, field))

    if not isinstance(model_field, models.ForeignKey):
        return False

    if model_class_from._meta.fields[field].related != model_class_to._meta.path_label:
        return False

    return True

def assert_model_class_fk(model_class_from, field, model_class_to):
    try:
        result = is_model_class_fk(model_class_from, field, model_class_to)
    except FieldDoesNotExist as e:
        print(e)
    else:
        if not result:
            print('Field %s.%s is not a ForeignKey to %s'%(
                model_class_from._meta.path_label,
                field.name,
                model_class_to._meta.path_label,
                ))

def is_free_fk(model_class_from, field):
    """Returns True if field is a ForeignKey with no specific relation"""
    try:
        model_field = model_class_from._meta.fields[field]
    except KeyError:
        raise FieldDoesNotExist('Model class "%s" has no declared field "%s"'%(model_class_from._meta.path_label, field))

    if not isinstance(model_field, models.ForeignKey):
        return False

    return not model_class_from._meta.fields[field].related

def assert_free_fk(model_class_from, field):
    try:
        result = is_free_fk(model_class_from, field)
    except FieldDoesNotExist as e:
        print(e)
    else:
        if not result:
            print('Field %s.%s is not a free ForeignKey'%(model_class_from._meta.path_label, field.name))

def assert_status_code(url, status_code, client=None):
    """Checks if the informed URL returns the wanted status_code"""
    if not client:
        from london.test.client import Client
        client = Client()

    resp = client.get(url)

    if status_code != resp.status_code:
        print('Expected status code %s is different of received: %s'%(status_code, resp.status_code))

def assert_approximated_numbers(n1, n2, tolerance=0.1):
    n1, n2 = float(n1), float(n2)
    if min([n1,n2]) / max([n1,n2]) < 1 - tolerance:
        print('%s is not aproximated to %s' % (n1,n2))

