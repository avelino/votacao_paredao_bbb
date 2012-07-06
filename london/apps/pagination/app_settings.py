from london.conf import settings

OBJECTS_PER_PAGE = getattr(settings, 'PAGINATION_OBJECTS_PER_PAGE', 10)

