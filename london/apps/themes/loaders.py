from jinja2.loaders import BaseLoader
from jinja2.exceptions import TemplateNotFound as JinjaTemplateNotFound

from london.exceptions import ImproperlyConfigured
from london.conf import settings
from london.apps.cache import cache
from london.utils.imports import import_anything

from datetime import datetime

import app_settings
from models import Theme, ThemeTemplate
from registration import get_registered_template

from os.path import getmtime

class Loader(BaseLoader):

    def get_source(self, environment, template):
        if ':' in template:
            active_theme, template_name = template.split(':', 1)
            active_theme = Theme.query().get(name=active_theme)
        elif getattr(environment, 'theme', None):
            template_name = template
            active_theme = environment.theme
        else:
            template_name = template
            active_theme = None
            if app_settings.CACHE_EXPIRATION:
                try:
                    active_theme = Theme.query().get(pk=cache.get('themes:active', None))
                except Theme.DoesNotExist:
                    pass

            if not active_theme:
                try:
                    theme = Theme.query().get(is_default=True)
                    if app_settings.CACHE_EXPIRATION:
                        cache.set('themes:active', theme['pk'], app_settings.CACHE_EXPIRATION)
                    active_theme = theme
                except Theme.DoesNotExist:
                    #raise JinjaTemplateNotFound('There\'s no active theme.')
                    pass

        try:
            reg_template = get_registered_template(template)
        except KeyError:
            if app_settings.ALLOW_NOT_REGISTERED:
                reg_template = {}
            else:
                raise JinjaTemplateNotFound('Template "%s" is not registered.'%template)

        content = None
        uptodate = lambda: True
        full_name = None
        engine = None
        if active_theme:
            try:
                # Using cache to restore/store template content
                cache_key = 'themes:%s|%s'%(active_theme['name'], template_name)
                content = cache.get(cache_key, None) if app_settings.CACHE_EXPIRATION else None

                if not content or not content.split(';',1)[-1] or content.split(';',1)[-1]=='None':
                    tpl = ThemeTemplate.query().get(theme=active_theme, name=template_name)
                    engine = tpl['engine']
                    content = tpl['content']
                    if app_settings.CACHE_EXPIRATION:
                        cache.set(cache_key, 'engine:%s;%s'%(engine,content or ''), app_settings.CACHE_EXPIRATION)

                full_name = '%s:%s'%(active_theme['name'], template_name)
            except ThemeTemplate.DoesNotExist:
                content = None

        if reg_template and not content:
            content = reg_template.get('content', None)

        if not content:
            if reg_template and reg_template.get('mirroring', None) and reg_template.get('mirroring', None) != template_name:
                # Trying this firstly...
                try:
                    return self.get_source(environment, reg_template['mirroring'])
                except JinjaTemplateNotFound as e:
                    pass

                # If get no success, tries by the hardest way, from file system...
                ret = environment.get_template(reg_template['mirroring'])
                if ret:
                    f = open(ret.filename)
                    try:
                        contents = f.read()
                    finally:
                        f.close()
                    return contents.decode('utf-8'), ret.filename, ret.is_up_to_date
            raise JinjaTemplateNotFound('Template "%s" doesn\'t exist in active theme.'%template_name)

        if content.startswith('engine:'):
            engine, content = content.split(';', 1)
            engine = engine.split(':')[1]

        return content, full_name, uptodate


def get_engine_class(path):
    if isinstance(path, basestring):
        module, attr = path.rsplit('.', 1)

        try:
            mod = import_anything(module)
        except ImportError as e:
            raise ImproperlyConfigured('Template engine "%s" was not found.'%path)

        try:
            return getattr(mod, attr)
        except AttributeError:
            raise ImproperlyConfigured('Template engine "%s" was not found.'%path)
