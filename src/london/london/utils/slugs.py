"""
The function "slugify" was copied from Django 1.4
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import re
from unicodedata import normalize 

def simplify_special_characters(txt, codif='utf-8'):
    """Replaces letters with accents to equivalent letters without accents.
    Thanks to Luciano Ramalho."""
    try:
        return normalize('NFKD', txt.decode(codif)).encode('ASCII','ignore')
    except UnicodeEncodeError:
        return normalize('NFKD', txt).encode('ASCII','ignore')

def slugify(value):
    """Returns a simple version of a given string, removing special characters and returning just
    numbers, letters, underscores and hifens. Replaces white spaces for hifens as well."""
    value = simplify_special_characters(value)
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

