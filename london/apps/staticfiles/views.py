import os
import mimetypes

from london.conf import settings
from london.http import HttpResponseNotFound, HttpResponse

def serve(request, path, root_dir):
    """
    A simple view to serve static files for development mode.
    """
    full_path = os.path.join(root_dir, path)
    if os.path.exists(full_path):
        fp = file(full_path, 'rb')
        content = fp.read()
        fp.close()

        try:
            mime_type = mimetypes.guess_type(full_path)[0]
        except IndexError:
            mime_type = 'unknown/unknown'

        return HttpResponse(content, mime_type=mime_type)
    else:
        return HttpResponseNotFound()

def url_serve(root_url, root_dir):
    """FIXME: this should be urls.py"""
    return (r'^%s(?P<path>.*)$'%root_url,
            serve,
            {'root_dir': root_dir},
            'staticfiles_server',
            )

