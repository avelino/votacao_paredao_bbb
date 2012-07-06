def _functionId(nFramesUp):
    """ Create a string naming the function n frames up on the stack.
    """
    import sys
    co = sys._getframe(nFramesUp+1).f_code
    return "%s (%s @ %d)" % (co.co_name, co.co_filename, co.co_firstlineno)


def _print_stack():
    import inspect
    print "====== stack =============="
    for frame,file,line,function,code,x in inspect.stack()[1:]:
        print file,line,function,code[0].strip()
    print "====== ===================="

