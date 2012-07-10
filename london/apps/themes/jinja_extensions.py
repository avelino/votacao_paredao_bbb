import hashlib

from jinja2.ext import Extension
from jinja2 import nodes

from london.conf import settings
from london.urls import reverse
from london.apps.themes.models import ThemeStaticFile, Theme

class ThemeExtension(Extension):
    tags = set(['theme_static_file'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'theme_static_file':
            return nodes.CallBlock(self.call_method('_tag_theme_static_file', args), [], [], []).set_lineno(lineno)

    def _tag_theme_static_file(self, name, caller):
        if ':' in name:
            theme_name, name = name.split(':')
            try:
                theme = Theme.query().get(name=theme_name)
            except Theme.DoesNotExist:
                theme = None
        else:
            theme = getattr(self.environment, 'theme', None)

        if not theme:
            return ''

        try:
            static = theme['static_files'].get(name=name)
        except ThemeStaticFile.DoesNotExist:
            return ''

        return static.get_url()

