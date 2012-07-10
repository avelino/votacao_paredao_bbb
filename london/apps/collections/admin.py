from london.apps import admin
from london.apps.collections.models import Collection
from london.apps.collections.forms import CollectionForm

class ModuleCollection(admin.CrudModule):
    model = Collection
    list_display = ('name', 'items', )
    form = CollectionForm 
    
class AppCollections(admin.AdminApplication):
    title = 'Collections'
    modules = (ModuleCollection, )
    