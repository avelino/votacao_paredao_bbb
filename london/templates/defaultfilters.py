from jinja2 import environmentfilter, contextfilter, evalcontextfilter, escape

@environmentfilter
def date(env, value, format):
    """
    You can use the Python date formatting string tokens to format a date or time
    """
    if not value:
        return ''
    return unicode(value.strftime(format))

