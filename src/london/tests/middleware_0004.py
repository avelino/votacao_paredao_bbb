from london.http import HttpResponse, Http404

class TestMiddleware(object):
    def process_request(self, request):
        request.any_value = 'Marta'

        if request.path_info == '/not-existing-url/':
            return HttpResponse('Not found but returns')
        elif request.path_info == '/force-exception/':
            raise ValueError('Wrong URL!')

    def process_response(self, request, response):
        if request.path_info == '/':
            return HttpResponse('The content')
        return response

    def process_exception(self, request, response, exception):
        if not isinstance(exception, Http404):
            return HttpResponse('The following error raised: '+unicode(exception))

