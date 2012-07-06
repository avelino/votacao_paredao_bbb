import sys
# FIXME: Deprecated since version 2.7: The optparse module is deprecated and
# will not be developed further; development will continue with the argparse
# module.
from optparse import make_option

from london.commands.base import BaseCommand
from london.services.utils import get_service, get_server
from london.core import load_apps
from london.utils import autoreload
from london.utils.imports import import_anything

DEFAULT_PROFILE_FILENAME = 'output.profile'


class Command(BaseCommand):
    """Runs the given web service listening to the configured port."""

    option_list = BaseCommand.option_list + [
        make_option('--server', action='store', dest='server',
            default='tornado',
            help='Accepts eventlet or tornado. Default is tornado.'),
        make_option('--disable-autoreload', action='store_true',
            dest='disable_autoreload', default=False,
            help='Set this to disable autoreloading after changes.'),
        make_option('--port', action='store', dest='port', default=None,
            help='Port to listen through.'),
        make_option('--profiling', action='store_true', dest='profiling',
            default=False,
            help=('Run the server under a profiler to measure the running '
                'time and resources usage.')),
        make_option('--profiling-file', action='store', dest='profiling_file',
            default=None, help='Outputs profiling to a file.'),
        make_option('--profiling-sort', action='store', dest='profiling_sort',
            default='calls', help=('Sets the column to sort profiling. Can be '
                'calls, cumulative, file, module, pcalls, line, name, nfl, '
                'stdname or time.')),
        make_option('--profiling-amount', action='store',
            dest='profiling_amount', default=None,
            help='Shows the amount of results set to this parameter.'),
        ]

    def execute(self, *args, **kwargs):
        self.port = kwargs.get('port',None)
        self.verbosity = kwargs['verbosity']

        self.server_class = {
                'gevent': 'london.services.servers.GeventServer',
                'eventlet': 'london.services.servers.EventletServer',
                'tornado': 'london.services.servers.TornadoServer',
                }.get(kwargs['server'])

        if kwargs.get('profiling', False):
            try:
                import cProfile as profile
            except ImportError:
                import profile

            filename = kwargs.get('profiling_file', DEFAULT_PROFILE_FILENAME)
            profile.runctx('run(settings, port, server_class, verbosity, *args)',
                globals(), {'settings':self.settings, 'port':self.port,
                'server_class':self.server_class, 'verbosity':self.verbosity,
                'args':args}, filename=filename,
                sort=kwargs.get('profiling_sort', -1))

            if filename == DEFAULT_PROFILE_FILENAME:
                import pstats
                stats = pstats.Stats(filename)
                inst = stats.sort_stats(kwargs.get('profiling_sort', 'calls'))
                inst.print_stats(kwargs.get('profiling_amount', 100))

        elif kwargs.get('disable_autoreload', False):
            run(self.settings, self.port, self.server_class, self.verbosity,
                *args)
        else:
            autoreload.main(run, (self.settings, self.port, self.server_class,
                self.verbosity)+args)

def run(settings, port, server_class, verbosity, *args):
    if verbosity >= 1:
        print('\nStarting a instance for the service "%s".'%args[0])

    # Loads installed applications
    for app in load_apps():
        if verbosity >= 1:
            print('Application %s loaded.'%app.__name__)

    # Running the service
    service = get_service(settings, args[0])
    service.port = int(port or service.port)

    server = get_server(server_class, service)
    server.run()

