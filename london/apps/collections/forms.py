from london import forms
from london.apps.collections import signals
from london.apps.collections.models import Collection


class CollectionForm(forms.ModelForm):

    class Meta:
        model = Collection
    
    def get_initial(self, initial=None):
        initial = initial or super(CollectionForm, self).get_initial(initial)
        signals.collections_form_initialize.send(sender=self, initial=initial)
        return initial

    def default_context(self, *args, **kwargs):
        return {
            'object_verbose_name': self._meta.model._meta.verbose_name,
            'object_verbose_name_plural': self._meta.model._meta.verbose_name_plural
        }