from london.apps import admin
from london.apps.themes.models import Theme, ThemeTemplate, ThemeStaticFile
from london import forms

class ModuleTheme(admin.CrudModule):
    model = Theme
    list_display = ('name','verbose_name','is_default',)

class ModuleThemeTemplate(admin.CrudModule):
    model = ThemeTemplate
    list_display = ('name','theme','engine',)

class FormThemeStaticFile(forms.ModelForm):
    class Meta:
        model = ThemeStaticFile

    def save(self, commit=True):
        if getattr(self.cleaned_data['file'], 'content_type', None):
            self.cleaned_data['mime_type'] = self.cleaned_data['file'].content_type

        return super(FormThemeStaticFile, self).save(commit=commit)

class ModuleThemeStaticFile(admin.CrudModule):
    model = ThemeStaticFile
    form = FormThemeStaticFile
    list_display = ('name','theme','mime_type',)

class AppThemes(admin.AdminApplication):
    title = 'Themes'
    modules = (ModuleTheme, ModuleThemeTemplate, ModuleThemeStaticFile)


