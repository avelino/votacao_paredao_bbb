"""
This application supplies authentication functions, including extendable model classes for Users, User Groups and their
Permissions, generic views and forms to be used for user registration, password changing, password reminders, password
strength, user authentication and logout functions, etc.
"""

from london.apps.auth.authentication import user_authenticate, user_logout, user_login
from london.apps.auth.authentication import login_required, permission_required
from london.apps.auth.exceptions import AuthenticationFailed
from london.templates.signals import template_global_context

