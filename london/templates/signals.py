from london.dispatch import Signal

template_global_context = Signal(required=('request',))
get_template_loaders = Signal()

