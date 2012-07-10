#!/usr/bin/env python
import os
import sys
import imp
import pdb
from optparse import OptionParser

from london import get_version
from london import commands
from london.commands.base import basic_option_list
from london.conf import settings
from london.utils.imports import import_anything

sys.path.insert(0, os.getcwd())

def get_subcommand(cmd):
    if cmd == 'run':
        cmd = 'runserver'
    return cmd

class BasicOptionParser(OptionParser):
    def error(self, msg):
        pass

def get_option_parser(option_list, cls=OptionParser, **kwargs):
    parser = cls(
            usage='%prog subcommand [options] [args]',
            version=get_version(),
            option_list=option_list,
            **kwargs
            )
    return parser.parse_args(sys.argv) # options, args

def execute():
    # Arguments parser
    options, args = get_option_parser(basic_option_list, cls=BasicOptionParser, add_help_option=False)
    settings.project_settings = import_anything(options.settings)

    # Command parsing
    subcommand = get_subcommand(sys.argv[1])
    command_class = None
    
    # Find the command in the command directories
    for path in commands.get_commands():
        if path.endswith('.'+subcommand):
            try:
                command_class = import_anything(path+'.Command')
                break
            except ImportError:
                pass

    # If the command doesn't exist...
    if not command_class:
        print('Command not found.')
        sys.exit(1)

    # Arguments parser
    options, args = get_option_parser(command_class.option_list)

    if options.run_with_pdb:
        pdb.set_trace()

    kwargs = dict([(opt.dest, getattr(options, opt.dest, opt.default))
        for opt in command_class.option_list])
    
    # Running the command
    cmd = command_class(settings.project_settings)
    cmd.execute(*args[2:], **kwargs)

if __name__ == '__main__':
    execute()

