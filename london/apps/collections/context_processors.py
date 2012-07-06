from models import Collection
from render import get_collection_items

def basic(request):
    return {'collection_items': get_collection_items(request.site)}