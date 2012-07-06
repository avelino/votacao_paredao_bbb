def make_title(txt):
    """Just replaces underscors for white spaces and calls strin's method 'title'."""
    return txt.replace('_',' ').title()

def split_title(s):
    """
    Returns a string with spaces before upper letters, like: "Regular Locations" for "RegularLocations"
    """
    return ''.join([(' '+ch) if ch.isupper() else ch for ch in s]).strip()

