import sys

def import_anything(path, from_module=None):
    """Imports an object, class or module for given path"""
    
    if isinstance(path, (tuple, list)):
        path = '.'.join(path)

    # with module from
    if from_module:
        if isinstance(from_module, basestring):
            path = '%s.%s' % (from_module, path)
        else:
            path = '%s.%s' % (from_module.__name__, path)

    try:
        __import__(path)
        return sys.modules[path]
    except ImportError:
        if '.' in path:
            mod, attr = path.rsplit('.',1)
            try:
                __import__(mod)
                return getattr(sys.modules[mod], attr)
            except (ImportError, AttributeError):
                pass

    raise ImportError('No module named %s' % path)

