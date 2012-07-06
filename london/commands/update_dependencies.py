import os
import sys
import commands
from optparse import make_option

from london.commands.base import BaseCommand
from london.core import get_app
from london.utils.imports import import_anything
from london.conf import settings

class Command(BaseCommand):
    "Installs and/or upgrades depended packages."

    def execute(self, *args, **kwargs):
        self.verbosity = kwargs['verbosity']

        # Installs project needed packages
        for pkg in (settings.REQUIRED_PACKAGES or []):
            self.install_package(pkg)

        print('') # Line break

        # Third-part applications
        for name, entry in settings.INSTALLED_APPS.items():
            if kwargs['verbosity'] >= 1:
                print('Application "%s"'%name)

            # Installs the application
            if isinstance(entry, (list,tuple)) and len(entry) > 1 and entry[1]:
                self.install_package(entry[1])

            try:
                # Loads the application
                app = get_app(name)
                
                # Installs application needed packages
                for pkg in (getattr(app, 'REQUIRED_PACKAGES', None) or []):
                    self.install_package(pkg)
            except ImportError:
                pass

    def install_package(self, pkg):
        pip_bin = 'pip'

        status, output = commands.getstatusoutput('%s install -I %s'%(pip_bin, pkg))
        if self.verbosity >= 2:
            print(output)
        elif self.verbosity == 1:
            if status:
                print('Error when installing "%s"'%pkg)
            else:
                print('"%s" installed.'%pkg)

