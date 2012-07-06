"""
This application has a similar function of Django's contrib "messages", but works by a different point of view.

Notifications in this approach can be sent as cookies or by Ajax requests as well.
"""
from london.apps.notifications.api import *

import os
from london.apps.ajax import site
site.register_scripts_dir('notifications', os.path.join(os.path.dirname(__file__), 'scripts'))


