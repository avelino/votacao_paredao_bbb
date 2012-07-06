from london.forms import ModelForm

from models import Document

class FormDocument(ModelForm):
    class Meta:
        model = Document
        template = 'my_documents/edit.html'

    def get_instance(self, pk=None):
        return Document.query().get(pk=pk)

