import re

from london.conf import settings
from london.apps.mockups.models import MockupView
from london.http import HttpResponse
import app_settings

class MockupsMiddleware(object):
    def process_request(self, request):
        # Only for debug mode?
        if settings.DEBUG and not app_settings.ONLY_IN_DEBUG:
            return

        # Mockup views
        for mockup in MockupView.query().filter(is_active=True).order_by('creation_date'):
            match = re.match(mockup['url_pattern'], request.path_info)
            if not match:
                continue

            # Default response
            response = HttpResponse()
            response.content = mockup['content']
            response.status_code = mockup['status_code']
            response.headers.update(dict([l.split(':',1) for l in mockup['headers']]))
            response.mime_type = mockup['mime_type']

            # For given Python code
            if mockup['python_code']:
                code = []
                code.append('def func(request, *args, **kwargs):')
                code.extend(['    '+l for l in mockup['python_code'].split('\n')])
                code.append('response = func(request, *args, **kwargs)')
                global_vars = {'request': request, 'args':match.groups(), 'kwargs':match.groupdict()}
                local_vars = {} # This dictionary receives the response instance
                eval(compile('\n'.join(code), '<string>', 'exec'), global_vars, local_vars)

                if isinstance(local_vars['response'], HttpResponse):
                    response = local_vars['response']
                else:
                    response.content = local_vars['response']

            # For a raw uploaded file
            elif mockup['raw_file']:
                response.content = mockup['raw_file'].read()

            if response.status_code != 404:
                return response

