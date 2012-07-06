from london.conf import settings

def basic(request):
    if hasattr(request, 'site'):
        return {'current_site': request.site}
    else:
        return {}

