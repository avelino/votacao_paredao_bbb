from london.conf import settings
from london.db.connections import get_connection
from london.db.models.fields import *
from london.db.models.querysets import QuerySet, RelatedQuerySet
from london.db.models.base import BaseModel, Model, PersistentModel, NestedModel
from london.db.models.expressions import Sum, Max, Min, Count, Average

# Starts all available connections
# FIXME: this has to better to open only needed connections
for db in settings.DATABASES:
    get_connection(db)

