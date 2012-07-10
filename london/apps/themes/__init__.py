"""
Application responsible to keep customizable themes, templates and static files in database. This application supplies an API that
allows the developer to set which templates are customizable and how much it can be changed, like allowed variables, blocks and other
settings.

A theme is set to a site and once that site is loaded, the customized templates and static files are used instead of the original ones.

With this is possivel to have different layouts for the same project and choose which one to use based on the request, preview or
other criteria.
"""
import os
from london.apps.ajax import site
from london.apps.themes.jinja_extensions import ThemeExtension

site.register_styles_dir('themes', os.path.join(os.path.dirname(__file__), 'styles'))
site.register_scripts_dir('themes', os.path.join(os.path.dirname(__file__), 'scripts'))
