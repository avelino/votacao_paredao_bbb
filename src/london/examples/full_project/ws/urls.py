from london.urls.defining import patterns, include

url_patterns = patterns('ws.views',
        (r'^ws1/$', 'ws_handler', {}, 'ws_handler'),
        )

