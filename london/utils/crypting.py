"""
Many portions of code inside this file were copied from Django 1.4 and modified for our needs.
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import re
import hashlib
import hmac
from london.conf import settings

EXP_ENCRYPTED = re.compile('^(sha1|md5|crypt)\$(\w{12})\$(\w+)$')

class EncryptedString(object):
    """Encapsulates an encrypted string"""
    string = ''

    def __init__(self, string):
        self.string = string

    def __unicode__(self):
        return self.string

    def __str__(self):
        return self.string

    def __eq__(self, other):
        if isinstance(other, basestring):
            algo, salt, hsh = self.string.split('$')
            return self == EncryptedString.make(other, algo, salt)
        elif isinstance(other, EncryptedString):
            return self.string == other.string
        else:
            return False

    @classmethod
    def make(cls, raw_password, algo=settings.DEFAULT_ENCRYPT_ALGORITHM, salt=None):
        """This method is similar to Django's 'make_password', to make possible to work together
        with not pain."""
        if isinstance(raw_password, cls):
            return raw_password

        if EXP_ENCRYPTED.match(raw_password):
            return cls(raw_password)

        salt = salt or get_random_string()
        hsh = get_hexdigest(algo, salt, raw_password)
        return cls('%s$%s$%s'%(algo, salt, hsh))

def get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """This function was changed to work with same way of Django's function with same name."""
    import random
    try:
        random = random.SystemRandom()
    except NotImplementedError:
        pass    
    return ''.join([random.choice(allowed_chars) for i in range(length)])

def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    Copied from Django. All rights reserved.
    """
    raw_password, salt = raw_password, salt
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")

def salted_hmac(key_salt, value, secret=None):
    """
    Returns the HMAC-SHA1 of 'value', using a key generated from key_salt and a
    secret (which defaults to settings.SECRET_KEY).

    A different key_salt should be passed in for every application of HMAC.
    Copied from Django. All rights reserved.
    """
    if secret is None:
        secret = settings.SECRET_KEY

    # We need to generate a derived key from our base key.  We can do this by
    # passing the key_salt and our base key through a pseudo-random function and
    # SHA1 works nicely.
    key = hashlib.sha1(key_salt + secret).digest()

    # If len(key_salt + secret) > sha_constructor().block_size, the above
    # line is redundant and could be replaced by key = key_salt + secret, since
    # the hmac module does the same thing for keys longer than the block size.
    # However, we need to ensure that we *always* do this.
    return hmac.new(key, msg=value, digestmod=hashlib.sha1)

def constant_time_compare(val1, val2):
    """
    Returns True if the two strings are equal, False otherwise.

    The time taken is independent of the number of characters that match.
    Copied from Django. All rights reserved.
    """
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0

