import sys
import os

import london
from london.commands.base import BaseCommand

class Command(BaseCommand):
    """Run London Framework's own test suites and test scenarios. Needs to be using a full local copy and nose to work."""

    def execute(self, *args, **kwargs):
        from nose.core import TestProgram

        # The tests directory must be included in Python path to ensure test dependencies will be findable
        tests_dir = os.path.join(os.path.dirname(london.__path__[0]), 'tests')
        sys.path.insert(0, tests_dir)

        # Nose arguments
        argv = ['nosetests','--with-doctest','--doctest-extension=txt','--verbosity=2','--where='+tests_dir]

        # Nose program execution
        program = TestProgram(argv=argv, exit=False)

