from london.conf import settings

FILES_UPLOAD_TO = getattr(settings, 'MOCKUPS_FILES_UPLOAD_TO', 'mockup-view-files')
ONLY_IN_DEBUG = getattr(settings, 'MOCKUPS_ONLY_IN_DEBUG', True)

