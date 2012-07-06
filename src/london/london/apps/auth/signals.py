from london.dispatch import Signal

user_authenticate = Signal()
user_login = Signal(required=('request','users'))
user_is_logged = Signal(required=('request','caller'))
user_has_permission = Signal(required=('user','permission'), optional=('request',))

