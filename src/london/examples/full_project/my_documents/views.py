import datetime

from london.templates import render_template
from london.http import HttpResponseRedirect

from models import Document
from forms import FormDocument

@render_template('my_documents/home.html')
def home(request):
    documents = Document.query()
    return locals()

def create_document(request):
    now = datetime.datetime.now()

    document = Document()
    document['title'] = 'New document for %s'%now.strftime('%d/%m/%Y at %H:%M')
    document['content'] = 'This is a new document created to test our persistence framework'
    document.save()

    return HttpResponseRedirect('/my-documents/')

