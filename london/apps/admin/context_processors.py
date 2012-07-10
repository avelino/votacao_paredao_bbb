from london.conf import settings
from london.apps import admin
from london.apps.admin.app_settings import CURRENT_SITE_FILTER
from london.apps.sites.models import Site

def basic(request):
    ret = {'admin_site': admin.site}

    if getattr(request, 'session', None):
        # If there is a selected site
        if request.session.get(CURRENT_SITE_FILTER, None) is not None:
            ret['admin_selected_site'] = request.session[CURRENT_SITE_FILTER]
        else:
            if getattr(request, 'site', None):
                ret['admin_selected_site'] = str(request.site['pk'])
                request.session[CURRENT_SITE_FILTER] = str(request.site['pk'])
            else:
                sites = Site.query().active().filter(is_default = True)
    
                if sites.count() > 0:
                    ret['admin_selected_site'] = str(sites[0]['pk'])
                elif Site.query().active().count():
                    ret['admin_selected_site'] = str(Site.query().active()[0]['pk'])
                else:
                    ret['admin_selected_site'] = None

    return ret