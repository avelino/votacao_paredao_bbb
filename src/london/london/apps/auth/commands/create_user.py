import sys
from optparse import make_option

from london.commands.base import BaseCommand
from london.core import load_apps
from london.utils.slugs import slugify
from london.utils.crypting import get_random_string

class Command(BaseCommand):
    """Create a user to authenticate in the system using application london.apps.auth."""

    option_list = BaseCommand.option_list + [
        make_option('--username', action='store', dest='username', help='Username with no spaces'),
        make_option('--password', action='store', dest='password', help="User's password"),
        make_option('--email', action='store', dest='email', help="User's e-mail address"),
        make_option('--is-staff', action='store_true', dest='is_staff', default=False, help='Set the user to be able to access the admin area.'),
        make_option('--is-superuser', action='store_true', dest='is_superuser', default=False, help='Set the user to be able to have all permissions and to manage other users.'),
        ]

    def execute(self, *args, **kwargs):
        load_apps()

        from london.apps.auth.models import User

        if kwargs.get('username', None):
            if User.query().filter(username=kwargs['username']).count():
                sys.exit('User "%s" already exists.'%kwargs['username'])
        elif kwargs.get('email', None):
            if User.query().filter(email=kwargs['email']).count():
                sys.exit('User with e-mail "%s" already exists.'%kwargs['email'])
            kwargs['username'] = slugify(kwargs['email'])

        fields = {}

        # Username
        if kwargs.get('username', None):
            fields['username'] = kwargs['username']
        else:
            fields['username'] = raw_input('Username: ')
            if not fields['username'].strip():
                print('Invalid username.')
                sys.exit(1)

        # Password
        if kwargs.get('password', None):
            fields['password'] = kwargs['password']
        else:
            fields['password'] = raw_input('Password (empty for random generation): ')
            if not fields['password']:
                fields['password'] = get_random_string()
                print('The password "%s" was generated.'%fields['password'])
            elif fields['password'] != raw_input('... again, for confirmation: '):
                print('Password not apropriately confirmed.')
                sys.exit(1)

        # E-mail address
        if kwargs.get('email', None):
            fields['email'] = kwargs['email']
        else:
            fields['email'] = raw_input('E-mail address: ')
            if not fields['email'].strip():
                print('Invalid e-mail address.')
                sys.exit(1)

        # Is staff?
        if kwargs['is_staff']:
            fields['is_staff'] = kwargs['is_staff']
        else:
            fields['is_staff'] = raw_input('Can access admin (staff)?: ').lower() == 'yes'

        # Is superuser?
        if kwargs['is_superuser']:
            fields['is_superuser'] = kwargs['is_superuser']
        else:
            fields['is_superuser'] = raw_input('Superuser?: ').lower() == 'yes'

        # Checks if a user with that username already exists.
        if User.query().filter(username=fields['username']).count():
            print('Another user exists with the username "%s".'%fields['username'])
            sys.exit(1)
        
        user = User.query().create(**fields)
        print('The user "%s" was created with password "%s"'%(fields['username'], fields['password']))

