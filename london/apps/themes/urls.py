from london.urls.defining import patterns, include
from london.apps.auth.authentication import login_required

import views

# FIXME: login_required was disabled for all the URLs below. We need another solution because some systems don't use the same authentication functions to set
# a user as authenticated or not.

url_patterns = patterns('',
    (r'^$', views.home, {}, 'themes_home'),
    (r'^import/$', views.theme_import, {}, 'themes_import'),
    (r'^disable-preview/$', views.theme_preview, {}, 'themes_disable_preview'),
    (r'^(?P<name>[\w\-_]+)/$', views.theme, {}, 'themes_theme'),
    (r'^(?P<name>[\w\-_]+)/delete/$', views.theme_delete, {}, 'themes_delete'),
    (r'^(?P<name>[\w\-_]+)/set-default/$', views.theme_set_default, {}, 'themes_set_default'),
    (r'^(?P<name>[\w\-_]+)/preview/$', views.theme_preview, {}, 'themes_preview'),
    (r'^(?P<name>[\w\-_]+)/rename/$', views.theme_rename, {}, 'themes_rename'),
    (r'^(?P<name>[\w\-_]+)/save-as/$', views.theme_save_as, {}, 'themes_save_as'),

    (r'^(?P<name>[\w\-_]+)/up-file/$', views.theme_up_file, {}, 'themes_up_file'),  # FIXME: this must be fixed but at the moment it needs to be open to support our production system
    (r'^(?P<name>[\w\-_]+)/upload/$', views.theme_upload, {}, 'themes_upload'),     # /

    (r'^(?P<name>[\w\-_]+)/edit-child/$', views.theme_edit_child, {}, 'themes_edit_child'),
    (r'^(?P<name>[\w\-_]+)/delete-child/$', views.theme_delete_child, {}, 'themes_delete_child'),
    (r'^(?P<name>[\w\-_]+)/create-template/$', views.theme_create_template, {}, 'themes_create_template'),
    (r'^(?P<name>[\w\-_]+)/create-static-file/$', views.theme_create_static_file, {}, 'themes_create_static_file'),
    (r'^(?P<name>[\w\-_]+)/download/$', views.theme_download, {}, 'themes_download'),
)

