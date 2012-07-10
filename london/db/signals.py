from london.dispatch import Signal

model_get = Signal(required=('filters',))
model_list = Signal(required=('query',))
model_get_pk = Signal(required=('query','instance',))
model_clear_pk = Signal(required=('instance',))
model_list_delete = Signal(required=('query',))
model_list_count = Signal(required=('query',))
model_list_update = Signal(required=('query', 'items'))
model_pre_init = Signal(required=('model',)) # TODO
model_post_init = Signal(required=('model',)) # TODO

model_set_dependent = Signal(required=('dependent','depended','field',))
model_unset_dependent = Signal(required=('dependent','depended','field',))
model_get_dependents = Signal(required=('instance',))
model_register_dependents = Signal(required=('instance',))

nested_model_append = Signal(required=('instance','queryset',))
nested_model_remove = Signal(required=('instance','queryset',))

manytomany_model_append = Signal(required=('instance','queryset',))
manytomany_model_remove = Signal(required=('instance','queryset',))

pre_save = Signal(required=('instance',))               # Mostly used to clean values before to save them
model_save = Signal(required=('instance',))             # Mostly sent to database engines to store the object in database
post_save = Signal(required=('instance',))              # Used to do something after saving (like create a dependent, etc.)

pre_delete = Signal(required=('instance',))             # Used to do something before delete an object
model_delete = Signal(optional=('instance','filters',)) # Mostly sent to database engines to remove the object from database
post_delete = Signal(required=('instance',))            # Used to do something after delete an object

db_post_open = Signal(required=('connection',))

