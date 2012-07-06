import os
import hashlib

from london.apps.ajax import app_settings
from london.conf import settings
from london.apps.cache import cache

def minify(content, ext):
    """Uses YUICompressor to minify JavaScript and CSS content."""
    hsh = hashlib.sha1(content).hexdigest()
    cache_key = 'minify-'+hsh

    # Loads from cache
    ret = cache.get(cache_key, None)
    if ret: return ret

    jar_path = app_settings.YUICOMPRESSOR_PATH
    
    # Saves content in temporary file
    f_name = hsh
    f_path = os.path.join(settings.TEMP_DIR, '%s-all.%s'%(f_name, ext))
    new_path = os.path.join(settings.TEMP_DIR, '%s-min.%s'%(f_name, ext))
    fp = file(f_path, 'w')
    fp.write(content)
    fp.close()

    # Runs YUICompressor
    os.system("%s -o %s %s"%(jar_path, new_path, f_path))

    if app_settings.MINIFY and os.path.exists(new_path):
        # Checks if the minified file exists, otherwise returns the merged one
        fp = file(new_path)
        content = fp.read()
        fp.close()

    # Saves in cache
    cache.set(cache_key, content)

    return content

def minify_js(content):
    return minify(content, 'js')

def minify_css(content):
    return minify(content, 'css')

