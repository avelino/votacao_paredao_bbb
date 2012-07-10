from london.apps import admin
from london.apps.seo.models import Url, Rule, Analytics

class ModuleUrl(admin.CrudModule):
    model = Url
    list_display = ('pattern',)

class ModuleRule(admin.CrudModule):
    model = Rule
    list_display = ('robot','allowed','disallowed','crawl_delay',)
    exclude = ('sites',)
    
class ModuleAnalytics(admin.CrudModule):
    model = Analytics
    list_display = ('name',)

class AppSEO(admin.AdminApplication):
    title = 'SEO'
    modules = (ModuleUrl, ModuleRule, ModuleAnalytics)


