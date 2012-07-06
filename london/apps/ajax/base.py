import os
import glob
import time

from london.urls import patterns
from london.http import HttpResponse
from london.apps.ajax import app_settings
from london.apps.ajax.models import HashForTags
from london.utils.imports import import_anything
from london.utils.http import http_date
from london.templates import render_content

class AjaxSite(object):
    scripts = None
    styles = None

    def __init__(self, root_url=None):
        self.root_url = root_url

        self.scripts = {}
        self.styles = {}
        self.register_scripts_dir('ajax', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

    @property
    def urls(self):
        return patterns('',
                (r'^scripts/(?P<tags>[\w_\.\-\:,]+)/$', self.script_tags_view, {}, 'script_tags'),
                (r'^scripts/(?P<tags>[\w_\.\-\:,]+)/(?P<inc>\d+)/$', self.script_tags_view, {}, 'script_tags_inc'),
                (r'^styles/(?P<tags>[\w_\.\-\:,]+)/$', self.style_tags_view, {}, 'style_tags'),
                (r'^styles/(?P<tags>[\w_\.\-\:,]+)/(?P<inc>\d+)/$', self.style_tags_view, {}, 'style_tags_inc'),
                )

    def script_tags_view(self, request, tags, inc=None):
        """
        This view can be called like this:

        /ajax/scripts/ajax:base,ajax:history,etc:etc/

        or like this:

        /ajax/scripts/6b6962d5b178232a8b8ebbad4ec9781e546221ff/

        The first situation is more elegant and explicit, but if you have a really long URL, it breaks the
        HTML rendering by the browser, so, we need a hash to represent it in cache.
        """
        if ':' not in tags: # Loads hash from cache
            try:
                tags = HashForTags.query().get(hash=tags)['full_path']
            except HashForTags.DoesNotExist:
                pass

        last_modified = 0
        content = []
        for tag in tags.split(','):
            tag = tag[:-3] if tag.endswith('.js') else tag
            path = self.scripts.get(tag, None)
            if not path:
                for k,v in self.scripts.items():
                    if k.endswith(':'+tag):
                        path = v

            if path:
                fp = file(path)
                file_content = fp.read()
                fp.close()

                file_content = render_content(unicode(file_content, errors='ignore'), request=request)
                content.append(file_content)
                last_modified = max([last_modified, os.path.getmtime(path)])

        content = self.minify_js(u'\n'.join(c for c in content))
        last_modified = http_date(last_modified)

        resp = HttpResponse(content, mime_type='text/javascript')
        if last_modified:
            resp['Last-Modified'] = last_modified
        return resp

    def minify_js(self, content):
        func = app_settings.JS_MINIFY_FUNCTION
        if not callable(func):
            func = import_anything(func)
        return func(content)

    def style_tags_view(self, request, tags, inc=None):
        if ':' not in tags: # Loads hash from cache
            try:
                tags = HashForTags.query().get(hash=tags)['full_path']
            except HashForTags.DoesNotExist:
                pass

        last_modified = 0
        content = []
        for tag in tags.split(','):
            tag = tag[:-4] if tag.endswith('.css') else tag
            path = self.styles.get(tag, None)
            if not path:
                for k,v in self.styles.items():
                    if k.endswith(':'+tag):
                        path = v

            if path:
                fp = file(path)
                file_content = fp.read()
                fp.close()

                file_content = render_content(unicode(file_content, errors='ignore'), request=request)
                content.append(file_content)
                last_modified = max([last_modified, os.path.getmtime(path)])

        content = self.minify_css(u'\n'.join(content))
        resp = HttpResponse(content, mime_type='text/css')
        if last_modified:
            resp['Last-Modified'] = http_date(last_modified)
        return resp

    def minify_css(self, content):
        func = app_settings.CSS_MINIFY_FUNCTION
        if not callable(func):
            func = import_anything(func)
        return func(content)

    def register_script(self, namespace, path):
        if path not in self.scripts.values():
            name = os.path.split(path)[1]
            name, ext = os.path.splitext(name)
            self.scripts['%s:%s'%(namespace, name)] = path

    def register_scripts_dir(self, namespace, scripts_path):
        for path in glob.glob(os.path.join(scripts_path, '*.js')):
            self.register_script(namespace, path)

    def register_style(self, namespace, path):
        if path not in self.styles.values():
            name = os.path.split(path)[1]
            name, ext = os.path.splitext(name)
            self.styles['%s:%s'%(namespace, name)] = path

    def register_styles_dir(self, namespace, styles_path):
        for path in glob.glob(os.path.join(styles_path, '*.css')):
            self.register_style(namespace, path)

site = AjaxSite()

