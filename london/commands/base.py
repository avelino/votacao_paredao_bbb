from optparse import make_option

basic_option_list = [
        make_option('--settings', action='store', dest='settings', default='settings',
            help='Inform the package name to load settings from.'),
        make_option('--verbosity', action='store', dest='verbosity', default='1', type="int",
            help='Inform the verbosity level.'),
        ]

class BaseCommand(object):
    option_list = basic_option_list + [
            make_option('--pdb', action='store_true', dest='run_with_pdb', default=False,
                help='Set this command to run by Python Debugger. Try pdb.help() for more details.'),
        ]

    def __init__(self, settings):
        self.settings = settings

    def execute(self, *args, **kwargs):
        pass
