import datetime
from london.http import HttpRequest, HttpResponseRedirect
from london.apps.ajax.tags import redirect_to
from london.apps.auth import app_settings
from london.apps.auth.models import User
from london.apps.auth import signals
from exceptions import AuthenticationFailed

class AnonymousUser(object):
    authenticated = False

    def __init__(self, authenticated=False):
        self.authenticated = authenticated

    def is_authenticated(self):
        return self.authenticated

def get_request(*args, **kwargs):
    # Supports method and function views
    if 'request' in kwargs:
        return kwargs['request']
    elif isinstance(args[0], HttpRequest):
        return args[0]
    elif isinstance(args[1], HttpRequest):
        return args[1]

def view_login_required(func=None, **kwargs):
    """Decorator for view functions to require an authenticated user."""
    if 'url' in kwargs:
        url = kwargs['url']() if callable(kwargs['url']) else kwargs['url']
    else:
        url = None

    url = url or app_settings.LOGIN_URL

    def _wrapper(func):
        def _inner(*args, **kwargs):
            request = get_request(*args, **kwargs)

            if not request.user.is_authenticated():
                return redirect_to(request, url, no_history=True)
                
            return func(*args, **kwargs)
        return _inner

    if func:
        return _wrapper(func)
    else:
        return _wrapper

def form_login_required(cls=None, **kwargs):
    """Decorator for form classes to require an authenticated user."""
    if 'url' in kwargs:
        url = kwargs['url']() if callable(kwargs['url']) else kwargs['url']
    else:
        url = None

    url = url or app_settings.LOGIN_URL

    def _wrapper(cls):
        @classmethod
        def _inner(cls, request):
            if not request.user.is_authenticated():
                return redirect_to(request, url, no_history=True)
        cls._view_wrapper = _inner
        return cls

    return _wrapper(cls) if cls else _wrapper

def login_required(*args, **kwargs):
    """
    Decorator for views and classes to require user authentication, and redirect to the login URL if there's
    no user authenticated.
    """
    if args and isinstance(args[0], type):
        return form_login_required(*args, **kwargs)
    else:
        return view_login_required(*args, **kwargs)

def check_user_permission(user, permission, **kwargs):
    return user.is_authenticated() and user.has_perm(permission)
signals.user_has_permission.connect(check_user_permission)

def permission_required(*perms, **kwargs):
    """
    Decorator for views to require not only an authenticated user, but also a user with a
    specific permission, otherwise, it redirects to the authentication form.

    You can inform more than one permission at once, it accepts one of them.
    """
    if 'url' in kwargs:
        url = kwargs['url']() if callable(kwargs['url']) else kwargs['url']
    else:
        url = None

    url = url or app_settings.LOGIN_URL

    def _wrapper(func):
        def _inner(*args, **kwargs):
            request = get_request(*args, **kwargs)

            perms_user_has = []
            for perm in perms:
                if any(signals.user_has_permission.send(user=request.user, permission=perm)):
                    perms_user_has.append(perm)

            if not perms_user_has:
                return redirect_to(request, url)
 
            return func(*args, **kwargs)
        return _inner
    return _wrapper

def user_login(request, users):
    return any(signals.user_login.send(request=request, users=users))

def default_user_login(request, users):
    if app_settings.DISABLE_DEFAULT_AUTHENTICATION:
        return

    # Accepts a list of users to do the login
    user = users[0] if isinstance(users, (tuple, list)) else users
    user['last_login'] = datetime.datetime.now()
    user.save()
    request.session['user'] = {
            'model_class':'%s.%s'%(user.__class__.__module__, user.__class__.__name__),
            'pk':user['pk'],
            }
    request.user = user

    return bool(request.user)
signals.user_login.connect(default_user_login)

def user_authenticate(**kwargs):
    ret = filter(bool, signals.user_authenticate.send(**kwargs))
    if not ret:
        raise AuthenticationFailed('Not found valid user.')
    return ret

def default_user_authentication(username=None, password=None, email=None, **kwargs):
    if app_settings.DISABLE_DEFAULT_AUTHENTICATION:
        return

    try:
        if not username and email:
            fields = {'email':email}
        else:
            fields = {'username':username}

        user = User.query().get(**fields)

        if user.is_valid_password(password):
            return user
    except User.DoesNotExist:
        pass
signals.user_authenticate.connect(default_user_authentication)

def user_logout(request):
    """Forces the user logout from current session"""
    del request.session['user']

