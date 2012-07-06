from london.apps.seo import app_settings
from london.utils.safestring import mark_safe
from london.utils.imports import import_anything

def basic(request):
    def canonical_url_tag():
        protocol = 'https' if request.is_secure() else 'http'
        host = request.site['hostname'] if getattr(request, 'site', None) else request.META['HTTP_HOST']
        query_string = ('?'+request.META['QUERY_STRING']) if request.META.get('QUERY_STRING','') else ''
        current_url = '%s://%s%s%s'%(protocol, request.META['HTTP_HOST'], request.path_info, query_string)

        canonical_url = None
        if app_settings.CANONICAL_URL_FUNCTION:
            try:
                func = import_anything(app_settings.CANONICAL_URL_FUNCTION)
                canonical_url = func(request)
            except ImportError:
                pass

        if not canonical_url:
            canonical_url = '%s://%s%s%s'%(protocol, host, request.path_info, query_string)

        if current_url != canonical_url:
            return mark_safe('<link rel="canonical" href="%s"/>'%canonical_url)
        else:
            return ''
    return {'canonical_url_tag': canonical_url_tag}

