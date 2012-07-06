def format(value, format_string):
    if not value:
        return ''
    return value.strftime(format_string)

