from london.apps import admin
from london.apps.sites.models import Site, SiteMirror

class ModuleSite(admin.CrudModule):
    model = Site
    list_display = ('name', 'hostname', 'is_active', 'is_default',)

class ModuleSiteMirror(admin.CrudModule):
    model = SiteMirror
    list_display = ('hostname', 'site',)

class AppSites(admin.AdminApplication):
    title = 'Site'
    modules = (ModuleSite, ModuleSiteMirror)

