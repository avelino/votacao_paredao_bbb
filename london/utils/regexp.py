import re

def replace_groups(pattern, args=None, kwargs=None):
    """
    This function takes a pattern with groups and replaces them with the given args and/or
    kwargs. Example:

    For a given pattern '/docs/(\d+)/rev/(\w+)/', args=(123,'abc') and kwargs={},
    returns '/docs/123/rev/abc/'.

    For '/docs/(?P<id>\d+)/rev/(?P<rev>\w+)/', args=() and kwargs={'rev':'abc', 'id':123}
    returns '/docs/123/rev/abc/' as well.

    For '/docs/(?P<filename>(\w+)\.(doc|odt|pages))' (groups inside a group), it just considers
    the the most outside one.

    For now, when both args and kwargs are given, raises a ValueError.
    """
    if args and kwargs:
        raise ValueError("Informed both *args and **kwargs it's not supported.")

    exp_kwarg = re.compile('^\(\?P<(\w+)>(.+)\)$') # Used to check named arguments

    new = ''
    cur_group = ''
    group_count = 0

    for ch in pattern:
        if ch == '(':
            group_count += 1
            cur_group += ch
        elif ch == ')':
            group_count -= 1
            cur_group += ch

            if not group_count:
                m_kwarg = exp_kwarg.match(cur_group)

                if m_kwarg and kwargs:
                    value = str(kwargs.pop(m_kwarg.group(1)))
                else:
                    value = str(args[0])
                    args = args[1:]

                if re.match('^%s$'%cur_group, value):
                    new += value
                    cur_group = ''
        elif group_count:
            cur_group += ch
        else:
            new += ch

    return new

