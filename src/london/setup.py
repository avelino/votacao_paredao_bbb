import london
import os
import sys

# Downloads setuptools if not find it before try to import
try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass

from setuptools import setup

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way. Copied from Django.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages = []
data_files = []
london_dir = 'london'

for dirpath, dirnames, filenames in os.walk(london_dir):
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]

    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))

    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])    

if sys.version_info[0] >= 3:
    install_requires = ['distribute', 'Jinja2', 'nose', 'PyDispatcher', 'BeautifulSoup4','python-money',
            'tornado','pymongo==2.1.1']
else:
    install_requires = ['distribute', 'Jinja2', 'nose', 'simplejson', 'PyDispatcher',
            'BeautifulSoup==3.2.0','python-money','tornado','pymongo==2.1.1']

setup(
    name='London',
    version=london.__version__,
    #url='',
    author=london.__author__,
    license=london.__license__,
    packages=packages,
    data_files=data_files,
    scripts=['london/bin/london-admin.py','london/bin/london-create-project.py'],
    install_requires=install_requires,
    #setup_requires=[],
    )

