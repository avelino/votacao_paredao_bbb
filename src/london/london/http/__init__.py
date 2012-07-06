"""
Some parts of the code inside this file were copied on Django 1.4.
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import sys
from london.utils.safestring import mark_safe

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

try:
    import http.cookies as Cookie
except ImportError:
    import Cookie

try:
    import json as simplejson
    JSONDecodeError = ValueError
except ImportError:
    import simplejson
    JSONDecodeError = simplejson.JSONDecodeError

try:
    from london.utils.xml_encoding import DictXml
except ImportError:
    pass

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

from london.utils.json_encoding import CustomJSONEncoder
from london.conf import settings
from london.utils.encoding import force_unicode
from london.utils.datastructures import MultiValueDict, ImmutableList
from london.http.multipartparser import MultiPartParser
from london.core.files import uploadhandler

try:
    unicode
except NameError:
    unicode = str

FRIENDLY_ERROR_FILLER = unicode('\n<!-- Just to reach more than 512 bytes required by IE and Chrome -->')*10

class QueryDict(MultiValueDict):
    data_type = None
    _mutable = True

    def __init__(self, data='', mutable=False, encoding=None):
        self._json_values = {}
        self._data = data

        if not encoding:
            encoding = settings.DEFAULT_CHARSET
        self.encoding = encoding

        if not self._data:
            self.data_type = 'empty'

        # JSON package
        if not self.data_type:
            try:
                self._json_values = simplejson.loads(self._data)
            except (JSONDecodeError, TypeError) as e:
                pass
            else:
                self.data_type = 'json'

        # HTTP query string standard
        if not self.data_type:
            keys_and_values = parse_qsl(self._data)
            if keys_and_values:
                for key, value in keys_and_values:
                    key = force_unicode(key, encoding, errors='replace')
                    if key.endswith('[]'):
                        key = key[:-2]
                    value = force_unicode(value, encoding, errors='replace')
                    self.appendlist(key, value)
                self.data_type = 'qsl'

        self._mutable = mutable

    def __repr__(self):
        rep = repr(self._json_values) if self.data_type == 'json' else super(MultiValueDict, self).__repr__() 
        return "<%s: %s>" % (self.__class__.__name__, rep)

    def __contains__(self, item):
        if self.data_type == 'json':
            return item in self._json_values
        else:
            return super(QueryDict, self).__contains__(item)

    def __getitem__(self, key):
        if self._json_values:
            return self._json_values[key]
        else:
            return super(QueryDict, self).__getitem__(key)

    def _get_encoding(self):
        if self._encoding is None:
            self._encoding = settings.DEFAULT_CHARSET
        return self._encoding
    def _set_encoding(self, value):
        self._encoding = value
    encoding = property(_get_encoding, _set_encoding)

    def appendlist(self, key, value):
        self._assert_mutable()
        key = str_to_unicode(key, self.encoding)
        value = str_to_unicode(value, self.encoding)
        super(QueryDict, self).appendlist(key, value)

    def _assert_mutable(self):
        if not self._mutable:
            raise AttributeError("This QueryDict instance is immutable")    

class HttpRequest(object):
    _read_started = False
    _post_input = None
    _upload_handlers = []
    _encoding = None
    _is_asynchronous = False
    service = None

    def __init__(self, env, service=None):
        self.META = env
        self.path_info = self.META['PATH_INFO']
        self.method = self.META['REQUEST_METHOD']
        self.content_type = self.META.get('CONTENT_TYPE', 'text/plain')
        self.service = service

        if 'COOKIES' in self.META:
            self.COOKIES = self.META['COOKIES']
        else:
            self.COOKIES = Cookie.SimpleCookie(self.META.get('HTTP_COOKIE',''))

        self.GET = QueryDict(self.META.get('QUERY_STRING', ''))
        self._post_input = self.META.get('POST_INPUT', None)
        self._post_parse_error = False

    def __getitem__(self, key):
        key = key.lower()
        if self.method == 'GET':
            return self.GET.get(key, self.POST.get(key))
        else:
            return self.POST.get(key, self.GET.get(key))

    def _get_encoding(self):
        return self._encoding
    encoding = property(_get_encoding)

    def write(self, data):
        if self.META.get('ASYNC_WRITE', None):
            return self.META['ASYNC_WRITE'](data)
        else:
            raise NotImplementedError('Method "write" not implemented')

    def run_with_timeout(self, seconds, func, *args, **kwargs):
        if self.META.get('ASYNC_TIMEOUT', None):
            return self.META['ASYNC_TIMEOUT'](seconds, func, *args, **kwargs)
        else:
            raise NotImplementedError('Method "run_with_timeout" not implemented')

    def finish(self):
        if self.META.get('FUNCTION_FINISH', None):
            return self.META['FUNCTION_FINISH']()
        else:
            raise NotImplementedError('Method "finish" not implemented')

    def is_ajax(self):
        return self.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def get_full_path(self):
        return mark_safe(self.path_info + ('?'+self.META['QUERY_STRING'] if self.META.get('QUERY_STRING', None) else ''))

    def get_absolute_url(self):
        protocol = ("http", "https")['HTTP_X_FORWARDED_SSL' in self.META]
        return "%s://%s/" % (protocol, self.META['HTTP_HOST'])

    def is_secure(self):
        return self.META.get("HTTPS", None) == "on"

    def _load_post_and_files(self):
        # Populates self._post and self._files
        if self.method not in ('POST','PUT'):
            self._post, self._files = QueryDict('', encoding=self._encoding), MultiValueDict()
            return
        if self._read_started and not hasattr(self, '_raw_post_data'):
            self._mark_post_parse_error()
            return
        if self.META.get('CONTENT_TYPE', '').startswith('multipart'):
            data = StringIO(self.raw_post_data)
            try:
                self._post, self._files = self.parse_file_upload(self.META, data)
            except:
                # An error occured while parsing POST data.  Since when
                # formatting the error the request handler might access
                # self.POST, set self._post and self._file to prevent
                # attempts to parse POST data again.
                # Mark that an error occured.  This allows self.__repr__ to
                # be explicit about it instead of simply representing an
                # empty POST
                self._mark_post_parse_error()
                raise
        else:
            self._post, self._files = QueryDict(self.raw_post_data, encoding=self._encoding), MultiValueDict()

    def _mark_post_parse_error(self):
        self._post = QueryDict('')
        self._files = MultiValueDict()
        self._post_parse_error = True

    def parse_file_upload(self, META, post_data):
        """Returns a tuple of (POST QueryDict, FILES MultiValueDict)."""
        self.upload_handlers = ImmutableList(
            self.upload_handlers,
            warning = "You cannot alter upload handlers after the upload has been processed."
        )
        parser = MultiPartParser(META, post_data, self.upload_handlers, self.encoding)
        return parser.parse()

    def _get_raw_post_data(self):
        if not hasattr(self, '_raw_post_data'):
            if self._read_started:
                raise Exception("You cannot access raw_post_data after reading from request's data stream")
            self._raw_post_data = self.read()
            self._stream = StringIO(self._raw_post_data)
        return self._raw_post_data
    raw_post_data = property(_get_raw_post_data)    

    def read(self, *args, **kwargs):
        self._read_started = True
        if self._post_input:
            return self._post_input.read(*args, **kwargs)
        return ''

    def _initialize_handlers(self):
        self._upload_handlers = [uploadhandler.load_handler(handler, self)
                                 for handler in settings.FILE_UPLOAD_HANDLERS]

    def _set_upload_handlers(self, upload_handlers):
        if hasattr(self, '_files'):
            raise AttributeError("You cannot set the upload handlers after the upload has been processed.")
        self._upload_handlers = upload_handlers

    def _get_upload_handlers(self):
        if not self._upload_handlers:
            # If there are no upload handlers defined, initialize them from settings.
            self._initialize_handlers()
        return self._upload_handlers

    upload_handlers = property(_get_upload_handlers, _set_upload_handlers)

    def _get_post(self):
        if not hasattr(self, '_post'):
            self._load_post_and_files()
        return self._post
    def _set_post(self, post):
        self._post = post
    POST = property(_get_post, _set_post)

    def _get_files(self):
        if not hasattr(self, '_files'):
            self._load_post_and_files()
        return self._files
    FILES = property(_get_files)

    def _get_is_asynchronous(self):
        return self._is_asynchronous
    def _set_is_asynchronous(self, value):
        self._is_asynchronous = value
        if callable(self.META.get('FUNCTION_SET_ASYNC', None)):
            self.META['FUNCTION_SET_ASYNC'](value)
    is_asynchronous = property(_get_is_asynchronous, _set_is_asynchronous)

class WSGIRequest(HttpRequest):
    pass

class WebSocketRequest(HttpRequest):
    def __init__(self, ws, service=None):
        self.ws = ws
        super(WebSocketRequest, self).__init__(ws.environ, service=service)

class HttpResponse(object):
    status_code = 200
    status_string = 'OK'
    content = None
    headers = None
    mime_type = 'text/html'
    _cookies = None

    def __init__(self, content='', mime_type=None, headers=None):
        self.content = content
        self.mime_type = mime_type or self.mime_type
        self.headers = headers or {}
        self._cookies = Cookie.SimpleCookie()

    def __getitem__(self, key):
        return self.headers[key.lower()]

    def __setitem__(self, key, value):
        self.headers[key.lower()] = value

    def get_status(self):
        return '%s %s'%(self.status_code, self.status_string)

    def get_headers(self):
        # Content type
        if self.mime_type:
            self.headers['Content-Type'] = self.mime_type
            if self.mime_type == 'text/html':
                self.headers['Content-Type'] += '; charset=utf-8'

        headers = list(self.headers.items())

        # Set Cookie
        for cookie in self._cookies.values():
            headers.append(cookie.output().split(': ',1))

        return tuple(headers)

    def read(self):
        if isinstance(self.content, HttpResponse):
            self.status_code = self.content.status_code
            self.status_string = self.content.status_string
            self.mime_type = self.content.mime_type
            self.headers.update(self.content.headers)
            self.content = self.content.content
        return self.content

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', domain=None,
            secure=None, httponly=False, comment=None):
        """
        Follows the same Django's standard for cookie setting. But uses Cookie package for that.
        """
        self._cookies[key] = value
        if max_age:
            self._cookies[key]['max-age'] = max_age
        if expires:
            self._cookies[key]['expires'] = expires
        if path:
            self._cookies[key]['path'] = path
        if domain:
            self._cookies[key]['domain'] = domain
        if secure:
            self._cookies[key]['secure'] = 'true'
        if httponly:
            self._cookies[key]['httponly'] = 'true'
        if comment:
            self._cookies[key]['comment'] = comment

    def has_header(self, header):
        """Case-insensitive check for a header."""
        return header.lower() in self.headers

    def write(self, data):
        self.content = self.content or ''
        self.content += data

    __contains__ = has_header

class ErrorHttpResponse(HttpResponse):
    def read(self):
        content = super(ErrorHttpResponse, self).read()
        content += FRIENDLY_ERROR_FILLER
        return content

class HttpResponseNotFound(ErrorHttpResponse):
    status_code = 404
    status_string = 'Not Found'

class HttpResponseServerError(ErrorHttpResponse):
    status_code = 500
    status_string = 'Server Error'

class HttpResponseExpectationFailed(ErrorHttpResponse):
    status_code = 417
    status_string = 'Expectation Failed'

class HttpResponseRedirect(HttpResponse):
    status_code = 302
    status_string = 'Found'

    def __init__(self, url):
        super(HttpResponseRedirect, self).__init__()
        self.headers['Location'] = url
        self.mime_type = None

class HttpResponsePermanentRedirect(HttpResponseRedirect):
    status_code = 301
    status_string = 'Moved Permanently'

class HttpResponseForbidden(ErrorHttpResponse):
    status_code = 403
    status_string = 'Forbidden'

class Http404(Exception):
    def __init__(self, request=None):
        self.request = request
        super(Http404, self).__init__()

class JsonResponse(HttpResponse):
    mime_type = 'application/json'

    def read(self):
        if not isinstance(self.content, basestring):
            return simplejson.dumps(self.content, cls=CustomJSONEncoder)
        else:
            return self.content


class XmlResponse(HttpResponse):
    mime_type = 'application/xml'

    def read(self):
        if not isinstance(self.content, basestring):
            xml = DictXml()
            return xml.dumps(self.content)
        return self.content


class HttpResponseNoContent(HttpResponse):
    status_code = 204
    status_string = 'No Content'

class HttpResponseBadRequest(ErrorHttpResponse):
    status_code = 400
    status_string = 'Bad Request'

class HttpVersionNotSupported(ErrorHttpResponse):
    status_code = 505
    status_string = 'Version Not Supported'

class HttpResponseNotAllowed(ErrorHttpResponse):
    status_code = 405
    status_string = 'Method Not Allowed'

    def __init__(self, permitted_methods):
        super(HttpResponseNotAllowed, self).__init__()
        self['Allow'] = ', '.join(permitted_methods).upper()

class HttpResponseUnauthorized(ErrorHttpResponse):
    status_code = 401
    status_string = 'Unauthorized'

    def __init__(self, *args, **kwargs):
        realm = kwargs.get('realm')
        if realm:
            del(kwargs['realm'])
        super(HttpResponseUnauthorized, self).__init__(*args, **kwargs)
        if realm:
            self['WWW-Authenticate'] = 'Basic realm="%s"' % realm

# It's neither necessary nor appropriate to use
# london.utils.encoding.smart_unicode for parsing URLs and form inputs. Thus,
# this slightly more restricted function.
def str_to_unicode(s, encoding):
    """
    Converts basestring objects to unicode, using the given encoding. Illegally
    encoded input characters are replaced with Unicode "unknown" codepoint
    (\ufffd).

    Returns any non-basestring objects without change.
    """
    if isinstance(s, str):
        return unicode(s, encoding, 'replace')
    else:
        return s

