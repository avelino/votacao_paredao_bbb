from london.apps import admin
from london.apps.mockups.models import MockupView

class ModuleMockupView(admin.CrudModule):
    model = MockupView
    list_display = ('url_pattern','status_code','force_https','is_active',)
    list_filter = ('status_code','force_https','is_active',)
    readonly_fields = ('creation',)

class AppMockups(admin.AdminApplication):
    title = 'Mockups'
    modules = (ModuleMockupView,)

