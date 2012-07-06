from london.apps import admin

from models import Document

class ModuleDocument(admin.CrudModule):
    model = Document
    list_display = ('title','is_published',)

class AppDocuments(admin.AdminApplication):
    title = 'Documents'
    modules = (ModuleDocument,)

