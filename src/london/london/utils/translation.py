from london.utils.functional import lazy
from london.conf import settings

def ungettext(singular, plural, number):
    return plural if number > 1 else singular

def ugettext(s):
    return s

def pgettext(context, message):
    return ugettext(message)

try:
    unicode
except NameError:
    unicode = str

ugettext_lazy = lazy(ugettext, unicode)
pgettext_lazy = lazy(pgettext, unicode)

def to_locale(language, to_lower=False):
    """
    Copied from Django 1.4.
    Copyright (c) Django Software Foundation and individual contributors. All rights reserved.

    Turns a language name (en-us) into a locale name (en_US). If 'to_lower' is
    True, the last component is lower-cased (en_us).
    """
    p = language.find('-')
    if p >= 0:
        if to_lower:
            return language[:p].lower()+'_'+language[p+1:].lower()
        else:
            # Get correct locale for sr-latn
            if len(language[p+1:]) > 2:
                return language[:p].lower()+'_'+language[p+1].upper()+language[p+2:].lower()
            return language[:p].lower()+'_'+language[p+1:].upper()
    else:
        return language.lower()

def get_language():
    # TODO: when we have a I18N support, this will be changed to work with the app i18n
    return settings.LANGUAGE_CODE

def check_for_language(lang_code):
    # FIXME
    return True

