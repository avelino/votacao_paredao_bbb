#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import commands


class LondonStart:

    SETUPTOOLS_URL = 'http://pypi.python.org/packages/source/d/distribute/distribute-0.6.24.tar.gz'
    SETUPTOOLS_NAME = SETUPTOOLS_URL.rsplit('/', 1)[-1]
    SETUPTOOLS_DIR = SETUPTOOLS_NAME.rsplit('.', 2)[0]
    LONDON_DEV_REPO = '-e git+git@github.com:mochii/london.git#egg=london'
    LONDON_BIN_DIR = os.path.dirname(os.path.abspath(__file__))
    OPTIONAL_PACKAGES = ('tornado', 'pymongo==2.1.1', 'ipython')

    @property
    def get_version_os(self):
        return sys.version_info[0]

    @property
    def TEMP_DIR(self):
        if self.get_version_os == 'win32':
            return os.path.join(self.project_dir, 'tmp')
        return '/tmp/'

    def install_initial_dependencies(self, project_dir):
        self.project_dir = project_dir
        os.chdir(self.TEMP_DIR)

        # setuptools
        try:
            import setuptools
        except ImportError:
            print('.. setuptools')
            commands.getoutput('curl -s %s >%s%s' % (self.SETUPTOOLS_URL,
                self.TEMP_DIR,
                self.SETUPTOOLS_NAME))
            os.chdir(self.TEMP_DIR)
            commands.getoutput('tar xvfz ' + self.SETUPTOOLS_NAME)
            os.chdir(os.path.join(self.TEMP_DIR, self.SETUPTOOLS_DIR))
            commands.getoutput('sudo python setup.py install')
            if self.get_version_os == 'win32':
                os.rmdir(self.TEMP_DIR)

        # pip
        try:
            import pip
        except ImportError:
            print('.. pip')
            commands.getoutput('sudo easy_install pip')

        # virtualenv
        try:
            import virtualenv
        except ImportError:
            print('.. virtualenv')
            commands.getoutput('sudo pip install virtualenv==1.6.4')

    def install_optional_dependencies(self, bin_dir, packages=OPTIONAL_PACKAGES):
        pip_bin = os.path.join(bin_dir, 'pip')

        for pkg in packages:
            commands.getoutput('%s install -I %s' % (pip_bin, pkg))

    def valid_london_version(self, version):
        return bool(version.strip())

    def parse_london_package(self, version):
        if version == 'local':
            return os.path.join(self.LONDON_BIN_DIR, '..', '..')
        elif version == 'dev':
            return self.LONDON_DEV_REPO
        else:
            return 'london==' + version

    def install_london(self, bin_dir, london_version):
        london_package = self.parse_london_package(london_version)

        if london_version == 'local' and os.path.exists(os.path.join(london_package, 'setup.py')):
            prev_cur_dir = os.path.abspath(os.curdir)
            os.chdir(london_package)
            commands.getoutput('%s setup.py develop' % os.path.join(bin_dir, 'python'))
            os.chdir(prev_cur_dir)
            return

        commands.getoutput('%s install %s' % (os.path.join(bin_dir, 'pip'), london_package))

    def get_london_dir(self, bin_dir):
        return commands.getoutput('%s -c "import london; print(london.__path__[0])"' % os.path.join(bin_dir, 'python'))

    def get_project_template_dir(self, bin_dir, name='default'):
        london_path = self.get_london_dir(bin_dir)
        return os.path.join(london_path, 'project_templates', name)

    def create_basic_project(self, bin_dir, root_dir):
        tpl_dir = self.get_project_template_dir(bin_dir, 'default')
        for folder, folders, files in os.walk(tpl_dir):
            short_folder = folder[len(tpl_dir) + 1:]

            # Creates the folder if it doesn't exist
            dest_folder = os.path.join(root_dir, short_folder)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)

            # Copies the files into destination folder
            for filename in files:
                if not filename.startswith('.') and not filename.endswith('.pyc'):
                    shutil.copyfile(os.path.join(folder, filename), os.path.join(dest_folder, filename))

    def run_project_service(self, bin_dir, root_dir, service='public'):
        os.chdir(root_dir)
        os.system('%s run %s' % (os.path.join(bin_dir, 'london-admin.py'), service))

    def update_dependencies(self, bin_dir, root_dir):
        os.chdir(root_dir)
        os.system('%s update_dependencies' % os.path.join(bin_dir, 'london-admin.py'))
