"""
Application created to supply SEO related functions, like permanent redirections, keywords, robots, sitemaps, canonical URLs among
others.

SEO includes search engine driven optimizations, which include the best semantic practices in order to fulfill a cleaner and strict
website, following web standards and in a proper way for search engines.
"""

import os
import london
from london.apps.ajax import site
from london.apps.seo.jinja_extensions import SeoExtension
from london.apps.seo.widgets import LetterCounterTextarea
from models import MetaInfo

site.register_scripts_dir('seo', os.path.join(os.path.dirname(__file__), 'scripts'))

def add_meta_info_fields_to_sender_form(sender, initial):
    form = sender
    form.fields['meta_description'] = london.forms.TextField(name='meta_description', widget=LetterCounterTextarea(maximum=160), required=False)
    form.fields['meta_keywords'] = london.forms.TextField(name='meta_keywords', widget=LetterCounterTextarea(maximum=160), required=False)
    
    meta_obj = None
    try:
        meta_obj = MetaInfo.query().get(owner=form.instance)
    except:
        pass
    
    if meta_obj:
        initial['meta_description'] = meta_obj['meta_description']
        initial['meta_keywords'] = meta_obj['meta_keywords']    
    
def save_meta_info_from_sender_form(sender):
    new_meta_obj, new = MetaInfo.query().get_or_create(owner=sender.instance)
    new_meta_obj['meta_keywords']=sender.cleaned_data['meta_keywords']
    new_meta_obj['meta_description']=sender.cleaned_data['meta_description']
    new_meta_obj.save()