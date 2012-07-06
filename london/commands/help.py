import sys
import textwrap
from optparse import make_option

from london.commands.base import BaseCommand
from london.commands import get_commands
from london.utils.imports import import_anything

class Command(BaseCommand):
    """Shows all available commands and their help descriptions."""

    def execute(self, *args, **kwargs):
        commands = []

        # Finds command classes in available modules
        for cmd in get_commands():
            module = import_anything(cmd)
            cls = import_anything('Command', module)
            commands.append((cmd.split('.')[-1], module, cls))

        commands.sort(lambda a,b: cmp(a[0], b[0]))

        # Prints their details

        print('Available commands:')

        for cmd, module, cls in commands:
            print('\n%s' % cmd)

            help = ''
            if getattr(cls, 'help', None):
                help = cls.help
            elif cls.__doc__:
                help = cls.__doc__

            if help:
                help = textwrap.wrap(help, 80)
                print('  ' + '\n  '.join(help))

