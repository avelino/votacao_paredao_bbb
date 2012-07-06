from london.apps import admin
from london import forms
from london.apps.mailing.models import MessageTemplate, MailingConfiguration, SentMessage, MailingSchedule

class FormMailingConfiguration(forms.ModelForm):
    class Meta:
        model = MailingConfiguration

    def get_instance(self, pk=None, *args, **kwargs):
        obj = super(FormMailingConfiguration, self).get_instance(pk, *args, **kwargs)

        if obj:
            for name, field in obj.get_backend().configuration_fields():
                #self.fields[name] = field
                pass

        return obj

class ModuleMailingConfiguration(admin.CrudModule):
    model = MailingConfiguration
    list_display = ('name','is_enabled','backend','site',)

class ModuleMessageTemplate(admin.CrudModule):
    model = MessageTemplate
    list_display = ('name','subject',)

class ModuleSentMessage(admin.CrudModule):
    model = SentMessage
    list_display = ('pk','date_sent','backend','__unicode__',)

class ModuleMailingSchedule(admin.CrudModule):
    model = MailingSchedule
    list_display = ('time_fields','template','backend','context_function',)

class AppMailing(admin.AdminApplication):
    title = 'Mailing'
    modules = (ModuleMailingConfiguration, ModuleMessageTemplate, ModuleSentMessage, ModuleMailingSchedule)



