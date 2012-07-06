"""
Application responsible for the management of multiple sites and their respective addresses and themes in the same instance.

This application is useful to have many sites, each one with its own content, theme (including templates and static files), user
permissions, etc.

If the setting CURRENT_SITE_BY_HOST_NAME is True, the default stide detection will be done matching to the requested HOST by browser,
which means if we have two sites "xxx.com" and other "zzz.com", a request for "http://xxx.com/something/" will detect as for the
site "xxx.com" because of the hostname.

On the other hand, the detection can be done via a customized view, using the setting SITE_DETECTING_FUNCTION.

This application is often needed because many other applications depend on it or even some basic functions are related to it.
"""
