from london.urls.defining import patterns, include

url_patterns = patterns('my_documents.views',
        (r'^$', 'home', {}, 'my_documents_home'),
        (r'^create/$', 'create_document', {}, 'my_documents_create'),
        )

url_patterns += patterns('my_documents.forms',
        (r'^edit/(?P<pk>\w+)/$', 'FormDocument', {}, 'my_documents_edit_form'),
        )

