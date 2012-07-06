import datetime
from london.db import models
from london.conf import settings

class Permission(models.Model):
    codename = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    application = models.CharField(max_length=50, blank=True, db_index=True)
    models = models.CharField(max_length=50, blank=True, db_index=True)

    def __unicode__(self):
        return self['name']

class UserGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField('Permission', blank=True, related_name='user_groups')

    def __unicode__(self):
        return self['name']

class AbstractUser(models.Model):
    class Meta:
        abstract = True

    username = models.CharField(max_length=50)
    password = models.PasswordField(max_length=200, blank=True, algorithm=settings.DEFAULT_ENCRYPT_ALGORITHM)
    email = models.EmailField(blank=True, db_index=True)
    is_active = models.BooleanField(default=True, blank=True, db_index=True)
    last_login = models.DateTimeField(default=datetime.datetime.now, blank=True)

    def __unicode__(self):
        return self['username']

    def is_valid_password(self, raw_password):
        return self['password'] == raw_password

    def get_full_name(self):
        return self['username']

class User(AbstractUser):
    is_staff = models.BooleanField(default=False, blank=True)
    is_superuser = models.BooleanField(default=False, blank=True, db_index=True)
    permissions = models.ManyToManyField('Permission', blank=True, related_name='users')
    groups = models.ManyToManyField('UserGroup', blank=True, related_name='users')

    def has_perm(self, perm):
        perms = self['permissions']

        if '.' in perm:
            app, codename = perm.split('.',1)
            perms = perms.filter(application=app, codename=codename)
        else:
            perms = perms.filter(codename=perm)

        return bool(perms.count())

