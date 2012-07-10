from london.conf import settings

def basic(request):
    if hasattr(request, 'user'):
        return {'user': request.user}
    else:
        return {}

