from london.apps.auth.authentication import AnonymousUser
from london.utils.imports import import_anything

class AuthMiddleware(object):
    def process_request(self, request):
        """
        Loads the authenticated user from current session.
        """
        user_info = request.session.get('user')
        user = None
        if user_info and isinstance(user_info, dict) and 'pk' in user_info and 'model_class' in user_info:
            cls = import_anything(user_info['model_class'])
            try:
                user = cls.query().get(pk=user_info['pk'])
                user.is_authenticated = lambda: True
            except cls.DoesNotExist:
                user = None
        
        request.user = user or AnonymousUser(authenticated=False)

