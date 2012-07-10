from london.dispatch import Signal

pre_send = Signal(required=('message',))
post_send = Signal(required=('message','success',))

