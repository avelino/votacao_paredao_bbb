"""
Application responsible for the management of user sessions, using memory, database or file system based storages. A session is
created everytime a new request is done without a specific cookie.

The cookie name given by setting SESSION_COOKIE_NAME (default "london_session_key") stores the session ID. The middleware
SessionMiddleware is responsible to load the session according to that ID and store the serialized data in session when exists.

The authentication and admin needs this application to store current session data related to the logged user and filters.

A session engine can be chosen to determine the way to store and retrieve sessions and it can be customized for peculiar situations
as well.
"""

from london.apps.sessions.engines.db import SessionStore as SessionDB

