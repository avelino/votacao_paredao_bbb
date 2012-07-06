"""
Collections are a groups of items, can be groups of articles or groups of pages.
Where we have items of the installed applications and then we can group them or move them from the group.
This appilcation allow users to: 
* create a unlimited groups of items (example website with unlimited number of Blogs);
* create listings in the example of the articles can be used in a newspaper website;
* integrate collections( albums aka galleries);
* allow regular users ( copyeditors and media editors ) to use and create important parts of an website by themselves;
* get possibility webmasters/webdesigners (who don't have access to the server) to edit templates and use any collection in templates using template tags.
"""
import os
import london

from london.db import _registered_models
from london.db.utils import get_model
from london.apps.ajax import site
from london.apps.sites.models import Site
from london.apps.admin.app_settings import CURRENT_SITE_FILTER
from london.apps.collections.jinja_extensions import CollectionsExtension

from models import Collection
import app_settings


site.register_scripts_dir('collections', os.path.join(os.path.dirname(__file__), 'scripts'))
site.register_styles_dir('collections', os.path.join(os.path.dirname(__file__), 'styles'))

def add_collection_items_to_sender_form(sender, initial):
    form = sender
    
    items_choices_from_app_settings = []
    for path in app_settings.APPS_FOR_COLLECTION_APP:
        model = get_model(path)
        queryset = model.query()
        if 'site' in model._meta.fields and form.request.session[CURRENT_SITE_FILTER] != '':
            site = Site.query().get(pk = form.request.session[CURRENT_SITE_FILTER])
            queryset = queryset.filter(site=site)
        for item in queryset:
            items_choices_from_app_settings.append((str(item['pk']), "%s: %s: %s" % (item._meta.app_label, item._meta.model_label, item.__unicode__() )))
    
    form.fields['items'] = london.forms.ChoiceField(name='items', widget=london.forms.SelectMultiple, choices=tuple(items_choices_from_app_settings),  required=False, help_text='app: model: item')
    

def save_collection_items_from_sender_form(sender):
    obj, new = Collection.query().get_or_create(name=sender.instance)
    obj['items'] = sender.cleaned_data['items']    
    obj.save()

def add_collections_to_sender_form(sender, initial):
    form = sender
    collection_choices = tuple([ ( str(collection['pk']), collection['name'] ) for collection in Collection.query().values('pk', 'name', ) if collection['name'] ])
    
    form.fields['collections'] = london.forms.ChoiceField(name='collections', widget=london.forms.SelectMultiple, choices=collection_choices, required=False)
    
    # FIXME: initial should already have collections 
    initial['collections'] = [str(collection['pk']) for collection in Collection.query().filter(items__contains=form.instance.pk)]

def save_collections_from_sender_form(sender):
    form = sender

    obj_pk = str(form.instance['pk'])
    for choice in form.fields['collections'].choices:
        collection_pk = choice[0]
        collection = Collection.query().get(pk=collection_pk)
        collection_items = collection['items'] 
        if collection_pk in form.cleaned_data['collections'] and obj_pk not in collection_items:
            collection_items.append(obj_pk)
        elif collection_pk not in form.cleaned_data['collections'] and obj_pk in collection_items:
            collection_items.remove(obj_pk)
        collection['items'] = collection_items
        collection.save()