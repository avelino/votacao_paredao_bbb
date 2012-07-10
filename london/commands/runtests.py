import sys
import os
from nose.core import TestProgram
from optparse import make_option

import london
from london.commands.base import BaseCommand
from london.core import load_apps, get_app
from london.utils import autoreload
from london.exceptions import ApplicationNotFound
from london.conf import settings
from london.utils.crypting import get_random_string
from london.db.connections import get_connection

class Command(BaseCommand):
    """Run tests containing in current project and installed applications."""
    option_list = BaseCommand.option_list + [
        make_option('--coverage', action='store_true', dest='with_coverage',
            default=False,
            help='Uses coverage package (if installed) to show statistics on code coverage by tests.'),
        ]

    def execute(self, *args, **kwargs):
        if not args and not settings.TEST_DEFAULT_APPS:
            sys.exit('You must inform the application name to test. It can be a list of applications separated by commas.')

        # Setting test mode to the settings
        settings._TESTING = True

        # Sets a different database setting
        old_databases = settings.DATABASES.copy()
        for k in settings.DATABASES:
            settings.DATABASES[k]['name'] = settings.DATABASES[k]['name'] + '_test_' + get_random_string()

            # Creates the test database
            conn = get_connection(k, force_reopen=True)
            conn.create_database()

        # Default nose arguments
        argv = ['nosetests','--with-doctest','--verbosity=%s'%kwargs['verbosity']]
        if kwargs.get('with_coverage',None):
            argv.append('--with-coverage')
        if settings.TEST_ADDITIONAL_ARGS:
            argv.extend(settings.TEST_ADDITIONAL_ARGS)
        #if test_case:
        #    argv.append('--testmatch=%s\.txt'%test_case) # FIXME: it's not working

        # Gets informed application
        bits = (args[0] if args else settings.TEST_DEFAULT_APPS).split(',')
        for app in load_apps():
            if not [b for b in bits if b.split(':')[0] == app._app_in_london]:
                continue

            # TODO The sign ":" is for tell a specific test file instead of whole application. But this is not yet working.

            # Finds the test directory
            tests_dir = os.path.join(app.__path__[0], 'tests')
            if not os.path.exists(tests_dir):
                sys.exit('There is no folder "tests" in the given application.')

            sys.path.insert(0, tests_dir)
            argv.append('--where=' + tests_dir)

        # Finally, running the test program
        program = TestProgram(argv=argv, exit=False)

        # Drops the test databases
        for k in settings.DATABASES:
            conn = get_connection(k)
            conn.drop_database()

