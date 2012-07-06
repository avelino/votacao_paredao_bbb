import sys
import pymongo
from bson.dbref import DBRef

from optparse import make_option

from london.commands.base import BaseCommand
from london.core import load_apps
from london.conf import settings

class Command(BaseCommand):
    """Only for MongoDB databases. Loops on database objects changing DBRef to London's dictionary format for supporting additional keys."""

    option_list = BaseCommand.option_list + [
        make_option('--database', action='store', dest='database', default='default', help='Database key in DATABASE setting.'),
        make_option('--collections', action='store', dest='collections',
            help='Collections to convert separated by comma. Default is all collections.'),
        ]

    def execute(self, database, collections, *args, **kwargs):
        #load_apps()

        database = settings.DATABASES[database]['name']

        convert_collections(database, [s.strip(',') for s in collections.split(',')] if collections else '')

def convert_collections(database, collections):
    conn = pymongo.Connection()
    db = conn[database]

    if not collections:
        collections = db.collection_names()

    # Collections
    for collection in collections:
        coll = db[collection]

        print('%s (%s)' % (collection, coll.find().count()))

        # Objects
        for obj in coll.find():
            changed = {}

            # Field values
            for k,v in obj.items():
                if isinstance(v, DBRef):
                    changed[k] = {'_db_storage':v.collection, 'pk':v.id}
                    sys.stdout.write('.'); sys.stdout.flush()
                elif isinstance(v, dict) and '$id' in v and '$ref' in v:
                    changed[k] = {'_db_storage':v['$ref'], 'pk':v['$id']}
                    changed[k].update(v)
                    del changed[k]['$id']
                    del changed[k]['$ref']
                    sys.stdout.write('.'); sys.stdout.flush()

            if changed:
                coll.update({'_id': obj['_id']}, {'$set':changed})

        print('')

