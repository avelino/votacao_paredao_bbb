from london.conf import global_settings

class Settings(object):
    project_settings = None

    @property
    def INSTALLED_APPS(self):
        apps = self.project_settings.INSTALLED_APPS
        if isinstance(apps, (tuple, list)):
            return dict([(a.split('.')[-1],a) for a in apps])
        else:
            return apps

    def __getattr__(self, name):
        try:
            return getattr(self.project_settings, name)
        except AttributeError:
            return getattr(global_settings, name)

settings = Settings()

