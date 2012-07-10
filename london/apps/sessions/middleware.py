from london.apps.sessions import app_settings
from london.apps.sessions.base import get_session_class

class SessionMiddleware(object):
    def process_request(self, request):
        """
        Creates a session instance for the current user.
        """
        session = None
        session_store_class = get_session_class()

        if app_settings.COOKIE_NAME in request.COOKIES:
            session = session_store_class(
                key=request.COOKIES[app_settings.COOKIE_NAME].value,
                request=request,
                )

        if not session:
            session = session_store_class(request=request)

        request.session = session

    def process_response(self, request, response):
        """
        Sets the session cookie with its key
        """
        response.set_cookie(app_settings.COOKIE_NAME, request.session.key)

        if request.session and request.session.modified:
            request.session.save()

        return response

