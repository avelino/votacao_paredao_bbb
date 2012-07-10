#!/usr/bin/env python
"""
Syntax:

    curl http://london.org/london-start.py | python

    or

    python london-start.py

This script will:

    - Ask for the new project name
    - Ask for London version (stable release or development)
    - Install virtualenv
    - Create a new virtualenv box
    - Download and install london and dependencies
    - Create a new project, using SQLite
    - Ask to run the project public service
"""
from london.start.bootstrap import LondonStart
import os
import sys


def main():
    start = LondonStart()

    # Asks for new project name
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        print('> Please inform the project name:')
        project_name = raw_input()

    # Asks for the version of London
    if len(sys.argv) > 2:
        london_version = sys.argv[2]
    else:
        london_version = ''
        while not start.valid_london_version(london_version):
            print('> Which london of London you want to use? [dev]')
            print('  type the version number, "dev" for development version or "local" for installed version:')
            london_version = raw_input().lower() or 'dev'

    # Basic paths
    project_dir = os.path.join(os.path.abspath(os.curdir), project_name)
    root_dir = os.path.join(project_dir, 'root')
    bin_dir = os.path.join(project_dir, 'env', 'bin')
    pip_bin = os.path.join(bin_dir, 'pip')

    # Creates new project directory
    if os.path.exists(project_dir):
        project_exists = os.path.exists(root_dir)
    else:
        print('. Creating project directory...')
        project_exists = False
        os.makedirs(project_dir)

    # Installing dependencies
    print('. Installing dependencies...')
    start.install_initial_dependencies(project_dir)
    os.chdir(project_dir)

    # Creates the new virtualenv box
    if not os.path.exists(os.path.join(project_dir, 'env')):
        import virtualenv
        virtualenv.create_environment('env')

    # Installs London
    print('. Installing London framework...')
    start.install_london(bin_dir, london_version)

    # Installs optional packages
    print('. Installing optional packages...')
    start.install_optional_dependencies(bin_dir)

    if not project_exists:
        # Creates the new project folder from basic project template
        print('. Creating root directory...')
        os.makedirs(root_dir)

        # Creates basic template project
        print('. Creating basic project...')
        start.create_basic_project(bin_dir, root_dir)

    # Updates dependencies
    print('. Updating needed packages')
    start.update_dependencies(bin_dir, root_dir)

    # Run the public service
    print('. Now you can try on the browser:    http://localhost:8000/')
    print('')
    start.run_project_service(bin_dir, root_dir)

if __name__ == '__main__':
    main()
