import urllib
import Cookie

from london.conf import settings
from london.services.utils import get_service
from london.apps.auth.authentication import user_authenticate, user_login
from london.http import HttpRequest, HttpResponse

class Stream(object):
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

class Client(object):
    _cookies = None
    _session = None

    def __init__(self, service=None):
        self.service = service or 'public'
        if isinstance(self.service, basestring):
            self.service = get_service(settings, self.service)

        self._cookies = Cookie.SimpleCookie('')

    def _make_env(self, url, method, body=None, headers=None):
        env = {
            'HTTP_HOST': 'localtest',
            'PATH_INFO': url.split('?')[0],
            'QUERY_STRING': url.split('?')[1] if '?' in url else '',
            'REQUEST_METHOD': method,
            'CONTENT_TYPE': 'text/plain',
            'COOKIES': self._cookies,
            }
        if body:
            env['POST_INPUT'] = Stream(body)
        if headers:
            env.update(headers)
        return env

    def _request(self, url, method, body=None, headers=None):
        env = self._make_env(url, method, body, headers)
        resp = self.service.request_handle(env, self.start_response, return_response_object=True)

        for k,v in resp._cookies.items():
            if v:
                self._cookies[k] = v.value
            elif k in self._cookies:
                del self._cookies[k]

        if getattr(resp.request, 'session', None):
            if self._session:
                self._session.update(resp.request.session)
            else:
                self._session = resp.request.session

        return resp

    def get(self, url, headers=None):
        return self.treat_response(self._request(url, 'GET', headers=headers))

    def post(self, url, params=None, headers=None):
        params = params or {}
        return self.treat_response(self._request(url, 'POST', body=urllib.urlencode(params), headers=headers))

    def put(self, url, params=None, headers=None):
        params = params or {}
        return self.treat_response(self._request(url, 'PUT', body=urllib.urlencode(params), headers=headers))

    def delete(self, url, headers=None):
        return self.treat_response(self._request(url, 'DELETE', headers=headers))

    def treat_response(self, resp):
        if isinstance(resp.content, HttpResponse):
            return resp.content
        else:
            return resp

    def start_response(self, status_code, status_string):
        pass

    def login(self, **kwargs):
        # Fake request to have a standard response
        response = self._request('/', 'POST')
        
        # Users authentication (can be more than one because of many backends support
        users = user_authenticate(**kwargs)
        
        # Authentication return (True or False)
        ret = user_login(response.request, users)
        
        # Must save session
        response.request.session.save()

        return ret

    def logout(self):
        self._session = None

