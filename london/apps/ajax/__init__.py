"""
This application is responsible for supply projects and other applications with Ajax-rich functions, based on jQuery JavaScript
library.

It includes functions to control the navigation history, to bound up, compress and minify static blocks of code and template
tags related to it.
"""

from london.apps.ajax.minify import minify_js, minify_css
from london.apps.ajax.base import AjaxSite, site
from london.apps.ajax.jinja_extensions import AjaxExtension

