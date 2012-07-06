from jinja2.ext import Extension
from jinja2 import nodes

from london.urls import reverse

class LondonExtension(Extension):
    tags = set(['url'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'url':
            return nodes.CallBlock(self.call_method('_tag_url', args), [], [], []).set_lineno(lineno)
        elif token.value == 'autopaginate':
            if parser.stream.skip_if('comma'):
                args.append(parser.parse_expression())
            else:
                args.append(nodes.Const(None))
            
            return nodes.CallBlock(self.call_method('_tag_autopaginate', args), [], [], []).set_lineno(lineno)
        elif token.value == 'paginate':
            return nodes.CallBlock(self.call_method('_tag_paginate', args), [], [], []).set_lineno(lineno)

    def _tag_url(self, name, caller):
        return reverse(name)

