import sys
from optparse import make_option

from london.commands.base import BaseCommand
from london.core import load_apps
from london.db import _registered_models
from london.db.signals import model_register_dependents

class Command(BaseCommand):
    """Loops database objects from declared model classes and save them forcing dependent register to be safe."""

    option_list = BaseCommand.option_list + [
        make_option('--models', action='store', dest='models', default='', help='Model classes paths in "app.Model" format, separated by comma.'),
        ]

    def execute(self, models, *args, **kwargs):
        models = filter(bool, [m.strip() for m in models.split(',')])

        load_apps()

        for path, cls in _registered_models.items():
            if not hasattr(cls, 'query') or cls.query().count() == 0 or (models and path not in models):
                continue

            print('%s: %s objects' % (path, cls.query().count()))

            for obj in cls.query():
                sys.stdout.write('.'); sys.stdout.flush()
                model_register_dependents.send(instance=obj, for_all=True, sender=self)

            print('')

