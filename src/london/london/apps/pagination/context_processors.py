import app_settings
from london.http import Http404
from london.apps.pagination.paginator import Paginator, EmptyPage
from london.templates import render_to_string
from london.utils.safestring import mark_safe

def get_page_range(page_range, page_number, pages_around_current):
    """
    This function receives parameters with page range, current page number and the before/after count
    of pages to be around the current one and returns a list with a Digg-like range like this:

    1, None, 4, 5, 6, 7, 8, 9, 10, None, 20

    The None represents a gap and usually is shown as a "..." sign
    """
    page_number = int(page_number)
    if len(page_range) <= pages_around_current * 2 + 1: # N before + the current page + N after
        pages = page_range
    else:
        if page_number <= pages_around_current:
            pages = range(1, pages_around_current + page_number + 1)
        elif page_number >= page_range[-1] - pages_around_current:
            pages = range(page_number - pages_around_current, page_range[-1] + 1)
        else:
            pages = range(page_number - pages_around_current, page_number + 1 + pages_around_current)

        pages = list(set(pages))
        pages.sort()

        if pages[0] > 1:
            pages.insert(0, 1)
            if pages[1] > 2:
                pages.insert(1, None)
        if pages[-1] < page_range[-1]:
            pages.append(page_range[-1])
            if pages[-2] < page_range[-1] - 1:
                pages.insert(-1, None)
    return pages

class TemplatePaginator(Paginator):
    pages_around_current = 3

    def __init__(self, request, object_list, items_per_page, *args, **kwargs):
        self.request = request
        items_per_page = items_per_page or app_settings.OBJECTS_PER_PAGE
        super(TemplatePaginator, self).__init__(object_list, items_per_page, *args, **kwargs)

    def render(self, page_number=None):
        page_number = page_number or self.request.GET.get('_page', 1)
        try:
            page_obj = self.page(page_number)
        except EmptyPage:
            raise Http404
        pages = get_page_range(self.page_range, page_number, self.pages_around_current)
        query_params = self.request.META.get('QUERY_STRING','').split('&')
        query_params = '&'.join([q for q in query_params if not q.startswith('_page')])

        html = render_to_string(
            'pagination/pagination.html',
            {
                'pages': pages,
                'page_obj': page_obj,
                'paginator': self,
                'is_paginated': self.count > self.per_page,
                'query_params': '&'+query_params,
                },
            )
        return mark_safe(html)

    def get_list(self):
        page_number = self.request.GET.get('_page', 1)
        return self.page(page_number).object_list

def basic(request):
    def get_paginator(*args, **kwargs):
        return TemplatePaginator(request, *args, **kwargs)
    return {'get_paginator': get_paginator}

