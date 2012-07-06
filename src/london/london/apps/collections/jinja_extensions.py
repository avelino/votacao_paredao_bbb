from jinja2.ext import Extension
from jinja2 import nodes

from models import Collection

class CollectionsExtension(Extension):
    tags = set(['collection'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'collection':
            return nodes.CallBlock(self.call_method('_collection', args), [], [], []).set_lineno(lineno)
        
    def _collection(self, obj, caller):
        try:
            return "\r\n".join(Collection.query().get(name=obj)['items'] or [])
        except Collection.DoesNotExist:
            return ''