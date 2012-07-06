import re
import os
import imp
import glob

from london.conf import settings
from london.utils.imports import import_anything
from london.commands.base import BaseCommand

_commands_modules = None
def get_commands_modules():
    global _commands_modules

    if _commands_modules is not None:
        return _commands_modules

    _commands_modules = []

    # COMMANDS_DIRS
    if getattr(settings, 'COMMANDS_MODULES', None):
        _commands_modules.extend(settings.COMMANDS_MODULES)

    # Applications directories
    from london.core import load_apps
    for app in load_apps():
        path = os.path.join(app.__path__[0], 'commands')
        if os.path.exists(path):
            _commands_modules.append('%s.%s'%(app.__name__,'commands'))

    # This directory
    _commands_modules.append('london.commands')

    return _commands_modules

EXP_COMMAND = re.compile('^class Command\(', re.MULTILINE)

_commands = None
def get_commands():
    global _commands
    if _commands is not None:
        return _commands

    _commands = []

    for module in get_commands_modules():
        if isinstance(module, basestring):
            module = import_anything(module)

        for file_path in glob.glob(os.path.join(module.__path__[0], '*.py')):
            f_dir, f_name = os.path.split(file_path)
            if f_name.startswith('__init__.'):
                continue

            # Reading file to confirm that's a command
            fp = file(file_path)
            content = fp.read()
            fp.close()
            
            if EXP_COMMAND.search(content):
                _commands.append('%s.%s'%(module.__name__, os.path.splitext(f_name)[0]))

    return _commands

