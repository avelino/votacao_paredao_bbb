import os
from london.conf import settings

MINIFY = getattr(settings, 'MINIFY_SCRIPTS_AND_STYLES', True)
JS_MINIFY_FUNCTION = getattr(settings, 'JS_MINIFY_FUNCTION', 'london.apps.ajax.minify_js')
CSS_MINIFY_FUNCTION = getattr(settings, 'CSS_MINIFY_FUNCTION', 'london.apps.ajax.minify_css')
JAVA_PATH = getattr(settings, 'JAVA_PATH', 'java')
YUICOMPRESSOR_PATH = getattr(settings, 'YUICOMPRESSOR_PATH',
        JAVA_PATH + '  -jar ' + os.path.join(os.path.dirname(__file__), '..', '..', 'bin', 'yuicompressor-2.4.4.jar'))

