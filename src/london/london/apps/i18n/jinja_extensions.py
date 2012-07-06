from jinja2.ext import Extension
from jinja2 import nodes

from london.conf import settings
from london.urls import reverse
from london.utils.translation import ugettext

class I18nExtension(Extension):
    tags = set(['trans'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'trans':
            return nodes.CallBlock(self.call_method('_tag_trans', args), [], [], []).set_lineno(lineno)

    def _tag_trans(self, text, caller):
        # TODO: there is already the tag {% trans %}{% endtrans %} in jinja2.ext.i18n
        return ugettext(text)

