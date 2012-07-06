from london.conf import settings
from london.utils.imports import import_anything

_connections = {}
def get_connection(name='default', force_reopen=False):
    """
    Opens and/or returns a connection by name.
    """
    conn = _connections.get(name, None)

    if conn and force_reopen:
        if conn._connection:
            conn._connection.disconnect()
        del _connections[name]
        conn = None

    if not conn or not conn.is_open():
        db_params = settings.DATABASES[name]
        engine_class = import_anything(db_params['engine'])
        conn = _connections[name] = engine_class(**db_params)

    return conn

