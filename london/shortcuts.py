from london.http import Http404, JsonResponse, XmlResponse
from london.db import models
from london.exceptions import ObjectDoesNotExist
from london.templates import render_to_response

def get_object_or_404(class_or_queryset, **kwargs):
    """
    Gets an object from a model class or queryset, according to the criteria given as keys and values.
    If that object doesn't exist, it raises an Http404 response.
    """
    if isinstance(class_or_queryset, type) and issubclass(class_or_queryset, models.Model):
        qs = class_or_queryset.query()
    else:
        qs = class_or_queryset

    try:
        return qs.get(**kwargs)
    except ObjectDoesNotExist:
        raise Http404

def json_response(func):
    """
    Decorator to mark a view to return a JSON response.

    Usage:
        @json_response
        def view(request):
            return {...}
    """
    def _wrapper(request, *args, **kwargs):
        return JsonResponse(func(request, *args, **kwargs))
    return _wrapper

def xml_response(func):
    """
    Decorator to mark a view to return a XML response.

    Usage:
        @xml_response
        def view(request):
            return {...}
    """
    def _wrapper(request, *args, **kwargs):
        return XmlResponse(func(request, *args, **kwargs))
    return _wrapper

def accepted_methods(*permitted_methods):
    """
    Decorator to strict a view to allow only a set of methods, otherwise a 405 response is sent.
    
    Usage:
        @accepted_methods('post','put')
        def view(request):
            return {...}
    """
    permitted_methods = [m.lower() for m in permitted_methods]
    def _wrap(func):
        def _inner(request, *args, **kwargs):
            # Returns 405 (Method Not Allowed) response if the method is not in the list
            if request.method.lower() not in permitted_methods:
                return HttpResponseNotAllowed(permitted_methods)

            return func(request, *args, **kwargs)
        return _inner
    return _wrap

