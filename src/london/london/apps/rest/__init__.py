"""
This application has a similar function of Admin application but its end is to supply an API to construct REST API services.

That means a REST site is able to support authentications, like OAuth and others, filter by authorized External Applications and/or
external IPs, etc. REST modules are able to support HTTP methods like DELETE, PUT, GET and POST properly to let possible to create,
updated, query, delete and process database objects as resources.
"""

from london.apps.rest.base import RestSite
from london.apps.rest.modules import CrudModule

