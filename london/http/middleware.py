from london.conf import settings

class CORSMiddleware(object):
    """
    Implements CORS functions from HTTP protocol according to W3C: http://www.w3.org/TR/cors/
    """

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        if settings.CORS_ALLOWED_ORIGINS and not response.headers.get('Access-Control-Allow-Origin', None):
            response['Access-Control-Allow-Origin'] = ' '.join(settings.CORS_ALLOWED_ORIGINS)

        if settings.CORS_ALLOWED_CREDENTIALS and 'Access-Control-Allow-Credentials' not in response.headers:
            response['Access-Control-Allow-Credentials'] = 'true'

        return response

