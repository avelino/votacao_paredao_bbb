from london.apps import admin
from london.apps.redirects.models import Redirect

class ModuleRedirect(admin.CrudModule):
    model = Redirect
    list_display = ('site','url_pattern','url_destination','is_permanent',)

class AppRedirects(admin.AdminApplication):
    title = 'Redirect'
    modules = (ModuleRedirect,)

