from london import forms
from models import MetaInfo

class LetterCounterTextarea(forms.Textarea):
    class Media:
        js = ('scripts/seo:lettercounter/',)
    
    def __init__(self, *args, **kwargs):
        self.maximum = kwargs.pop('maximum')
        super(LetterCounterTextarea, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        attrs['class'] = 'vLargeTextField letter-counter'
        attrs['rel'] = str(self.maximum)
        return super(LetterCounterTextarea, self).render(name, value, attrs)