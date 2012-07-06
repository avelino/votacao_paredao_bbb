"""
Email message and email sending related helper functions.

Copied from Django 1.4
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""

import socket


# Cache the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn

DNS_NAME = CachedDnsName()
