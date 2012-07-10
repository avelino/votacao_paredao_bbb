from london.dispatch import Signal

# Signals called everytime an action changes a theme's static file or a bunch of them
theme_static_files_changed = Signal(required=('theme',))
theme_static_files_deleted = Signal(required=('theme',))

