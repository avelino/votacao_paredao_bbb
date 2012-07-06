import os
import sys
import commands

VERSION_NUMBER = '0.1'

_version = None
def get_version():
    global _version

    if _version is None:
        # Current directory kept in a variable to change again later, then changes to london's path
        curdir = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Checking this package is in a git repository (development version)
        status, commit_id = commands.getstatusoutput('git rev-parse --short HEAD')
        
        # status zero means git is installed and this path is in a git repository
        if status == 0:
            branch = commands.getoutput('git rev-parse --abbrev-ref HEAD')
            _version = '%(version)s (%(branch)s #%(commit_id)s)' % {
                    'version': VERSION_NUMBER,
                    'branch': branch,
                    'commit_id': commit_id,
                    }
        else:
            _version = VERSION_NUMBER

        os.chdir(curdir)

    return _version

