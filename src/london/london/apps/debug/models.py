from london.apps.admin import signals
from london.apps.debug.utils import get_process_info, get_memory_heap

def admin_stats(admin_site, request, **kwargs):
    boxes = []

    memory_heap = get_memory_heap()
    if memory_heap:
        boxes.append({'title':'Memory Heap', 'body':'<pre>%s</pre>' % memory_heap})

    process_info = get_process_info()
    if process_info:
        body = '<ul>%s</ul>' % ''.join(['<li>%s: %s</li>'%(k,v) for k,v in process_info])
        boxes.append({'title':'Process Info', 'body':body})

    return boxes
signals.collect_stats.connect(admin_stats)

