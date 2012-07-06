from jinja2.ext import Extension
from jinja2 import nodes

from models import Analytics, MetaInfo

class SeoExtension(Extension):
    tags = set(['analytics_scripts','meta_keywords_for','meta_description_for'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'analytics_scripts':
            return nodes.CallBlock(self.call_method('_analytics_script', args), [], [], []).set_lineno(lineno)
        elif token.value == 'meta_keywords_for':
            return nodes.CallBlock(self.call_method('_meta_keywords_for', args), [], [], []).set_lineno(lineno)
        elif token.value == 'meta_description_for':
            return nodes.CallBlock(self.call_method('_meta_description_for', args), [], [], []).set_lineno(lineno)
    
    def _analytics_script(self, tags, caller):
        # TODO: filter by current site
        # when m2m relations will be ready)
        #code_pieces = Analytics.query().on_site() 
        code_pieces = Analytics.query();
        if tags:
            names = tags.split(',')
            code_pieces = code_pieces.filter(name__in=names)
        code = code_pieces.values_list('code', flat=True)
        return "\r\n".join(code)
    
    def _meta_keywords_for(self, obj, caller):
        try:
            return MetaInfo.query().get(owner=obj)['meta_keywords'] or ''
        except MetaInfo.DoesNotExist:
            return ''
    
    def _meta_description_for(self, obj, caller):
        try:
            return MetaInfo.query().get(owner=obj)['meta_description'] or ''
        except MetaInfo.DoesNotExist:
            return ''

