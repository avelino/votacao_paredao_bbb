from london.dispatch import Signal

# Signal called to allow external applications to add buttons to a module form
module_form_buttons = Signal(required=('module','form',))

# Same as module_form_buttons, but used to links on the top of module form
module_form_links = Signal(required=('module','form',))

# Signal called to collect information to show in the stats page. Expets to receive a list with dictionaries
# similar to: {'order':0, 'title':'My Stats', 'body':'html code here'}
collect_stats = Signal(required=('admin_site','request',))

