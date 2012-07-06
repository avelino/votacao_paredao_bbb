from london.apps import admin
from london.apps.auth.models import User, Permission, UserGroup

class ModuleUser(admin.CrudModule):
    model = User
    list_display = ('username','email','is_staff',)
    exclude = ('permissions','groups')
    readonly_fields = ('last_login',)
    search_fields = ("username", "email")

class ModuleUserGroup(admin.CrudModule):
    model = UserGroup
    list_display = ('name',)
    exclude = ('permissions',)
    search_fields = ("name",)

class AppAuth(admin.AdminApplication):
    title = 'Authentication'
    modules = (ModuleUser, ModuleUserGroup)

