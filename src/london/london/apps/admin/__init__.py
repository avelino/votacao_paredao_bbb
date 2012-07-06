"""
This application is responsible for supply a RAD set of tools, especially for administration area. Most of the websites and
applications has a public and an administration areas, being the second one accessible only for users who has an account and
permission for.

An "Admin Site" is a root (usually "/admin/") where are installed a few applications when their modules. A project can have
more than one admin site, but it is not common. The admin site can be customized as much as possible, with different layout,
special pages and different kinds of modules.
"""

from london.apps.admin.base import AdminSite, AdminApplication
from london.apps.admin.modules import CrudModule, BaseModuleForm

site = AdminSite()
