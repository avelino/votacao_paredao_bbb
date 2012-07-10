import os
from london.apps.debug import app_settings

try:
    from subprocess import getoutput
except ImportError:
    from commands import getoutput

try:
    from guppy import hpy as guppy_hpy
except ImportError:
    guppy_hpy = None

PS_CMD = 'ps -p %s -o %%mem,%%cpu,vsz,rss,time' % os.getpid()

def get_process_info():
    if not app_settings.SEND_PROCESS_INFO:
        return {}
    
    output = getoutput(PS_CMD)
    header, line = output.split('\n')
    while '  ' in header: header = header.replace('  ',' ').strip()
    while '  ' in line: line = line.replace('  ',' ').strip()

    return list(zip(header.split(' '), line.split(' ')))

def get_memory_heap():
    if not app_settings.SEND_MEMORY_HEAP or not guppy_hpy:
        return ''

    return unicode(guppy_hpy().heap())

