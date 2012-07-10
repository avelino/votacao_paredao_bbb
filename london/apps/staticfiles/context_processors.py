from london.conf import settings

def basic(request):
    return {'STATIC_URL': settings.STATIC_URL}
