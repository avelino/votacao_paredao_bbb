import hashlib

from jinja2.ext import Extension
from jinja2 import nodes

from london.conf import settings
from london.urls import reverse
#from london.apps.ajax.base import site
from london.apps.ajax.models import HashForTags

class AjaxExtension(Extension):
    tags = set(['base','piece','container','container_mirror','style_tags','head_scripts',
        'body_scripts','require_script','style_url','script_url','raise'])

    def parse(self, parser):
        token = parser.stream.next()
        lineno = token.lineno
        args = [parser.parse_expression()]

        if token.value == 'base':
            return nodes.CallBlock(self.call_method('_tag_base', args), [], [], []).set_lineno(lineno)
        elif token.value == 'piece':
            body = parser.parse_statements(['name:endpiece'], drop_needle=True)
            return nodes.CallBlock(self.call_method('_tag_piece', args), [], [], body).set_lineno(lineno)
        elif token.value in ('container','container_mirror'):
            if parser.stream.skip_if('comma'):
                args.append(parser.parse_expression())
            else:
                args.append(nodes.Const(None))
            return nodes.CallBlock(self.call_method('_tag_container', args), [], [], []).set_lineno(lineno)
        elif token.value == 'style_tags':
            return nodes.CallBlock(self.call_method('_tag_style_tags', args), [], [], []).set_lineno(lineno)
        elif token.value in ('head_scripts','body_scripts'):
            return nodes.CallBlock(self.call_method('_tag_script_tags', args), [], [], []).set_lineno(lineno)
        elif token.value == 'style_url':
            return nodes.CallBlock(self.call_method('_tag_style_url', args), [], [], []).set_lineno(lineno)
        elif token.value == 'script_url':
            return nodes.CallBlock(self.call_method('_tag_script_url', args), [], [], []).set_lineno(lineno)
        elif token.value == 'raise':
            return nodes.CallBlock(self.call_method('_tag_raise', args), [], [], []).set_lineno(lineno)

    def _tag_base(self, template_name, caller):
        return '<base template_name="%s"/>'%template_name

    def _tag_piece(self, name, caller):
        body = caller()
        return '<piece name="%s">%s</piece>'%(name, body)

    def _tag_container(self, name, mirroring=None, caller=None):
        return '<div container="%s"%s id="%s"></div>'%(name, ' mirroring="%s"'%mirroring if mirroring else '',name)

    def _tag_style_tags(self, tags, caller):
        hsh = None
        if len(tags) > 40:
            full_path = tags
            tags = hashlib.sha1(tags).hexdigest()
            hsh, new = HashForTags.query().get_or_create(hash=tags, defaults={'full_path':full_path})
        url = reverse('style_tags_inc', kwargs={'tags':tags, 'inc':hsh['last_inc'] or 0 if hsh else 0})
        return '<link href="%s" rel="stylesheet"/>'%url

    def _tag_style_url(self, tags, caller):
        hsh = None
        if len(tags) > 40:
            full_path = tags
            tags = hashlib.sha1(tags).hexdigest()
            hsh, new = HashForTags.query().get_or_create(hash=tags, defaults={'full_path':full_path})
        return reverse('style_tags_inc', kwargs={'tags':tags, 'inc':hsh['last_inc'] or 0 if hsh else 0})

    def _tag_script_tags(self, tags, caller):
        hsh = None
        if len(tags) > 40:
            full_path = tags
            tags = hashlib.sha1(tags).hexdigest()
            hsh, new = HashForTags.query().get_or_create(hash=tags, defaults={'full_path':full_path})
        url = reverse('script_tags_inc', kwargs={'tags':tags, 'inc':hsh['last_inc'] or 0 if hsh else 0})
        return '<script src="%s" rel="%s" charset="utf-8"></script>'%(url, tags)
    
    def _tag_script_url(self, tags, caller):
        hsh = None
        if len(tags) > 40:
            full_path = tags
            tags = hashlib.sha1(tags).hexdigest()
            hsh, new = HashForTags.query().get_or_create(hash=tags, defaults={'full_path':full_path})
        return reverse('script_tags_inc', kwargs={'tags':tags, 'inc':hsh['last_inc'] or 0 if hsh else 0})

    def _tag_raise(self, tags, caller):
        raise Exception(tags)

