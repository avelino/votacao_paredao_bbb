import re

from london.db.utils import get_model

from models import Collection
from app_settings import APPS_FOR_COLLECTION_APP


def get_collection_items(site):
    def _get_collection_items(name):
        result = []
        try:
            for path in APPS_FOR_COLLECTION_APP:
                pk_items = Collection.query().get(name=name)['items']
                items = get_model(path).query().filter(pk__in=pk_items)
                result.extend(items)
                if items.count() == len(pk_items): # all items are of one model: no need to search items in other models
                    break
        except:
            pass
        return result
    return _get_collection_items