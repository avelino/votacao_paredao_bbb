import sys

from london.commands.base import BaseCommand
from london.core import load_apps

class Command(BaseCommand):
    """Open a interactive shell instance loading applications from framework and current project, and database connections."""

    def execute(self, *args, **kwargs):
        # Loads installed applications
        for app in load_apps():
            print('Application %s loaded.'%app.__name__)

        # Runs the shell istance
        shell = args[0] if args else 'ipython'
        try:
            getattr(self, shell)()
        except AttributeError:
            print('Invalid shell. Try "bpython", "ipython" or "notebook".')

    def bpython(self):
        try:
            import bpython
        except ImportError:
            sys.exit('You must install bpython to run this shell.')
        bpython.embed()

    def ipython(self):
        try:
            from IPython.frontend.terminal.embed import TerminalInteractiveShell
        except ImportError:
            sys.exit('You must install ipython to run this shell.')
        shell = TerminalInteractiveShell()
        shell.mainloop()

    def notebook(self):
        try:
            from IPython.frontend.html.notebook.notebookapp import launch_new_instance
            launch_new_instance()
        except ImportError:
            sys.exit('You must install ipython, tornado and pyzmq to run the notebook shell.')

