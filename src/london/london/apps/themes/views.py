import os
import mimetypes

from london.shortcuts import render_to_response, get_object_or_404
from london.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from london.conf import settings
from london.utils.slugs import slugify
from london.utils.translation import ugettext as _
from london.urls.finding import reverse
from london.apps.auth.authentication import permission_required
from london.db.models.fields.files import FieldFile
from london.core.files.base import ContentFile
from london.templates import render_template

from london.apps.themes import app_settings
from london.apps.themes.signals import theme_static_files_changed, theme_static_files_deleted
from london.apps.themes.packaging import export_theme, import_theme
from london.apps.themes.models import Theme, ThemeTemplate, ThemeStaticFile

#@permission_required('themes.change_theme')
def home(request):
    themes = Theme.query().order_by('verbose_name')
    previewing = request.COOKIES.get(app_settings.CURRENT_THEME_COOKIE, None)

    if request.POST.get('name', None):
        verbose_name = request.POST['name']
        name = slugify(request.POST['name'])
        counter = 0
        while Theme.query().filter(name=name).count():
            counter += 1
            name = '%s-%s'%(slugify(request.POST['name']), counter)
        theme = Theme.query().create(name=name, verbose_name=verbose_name)

        request.warning(_('New theme "%s" created.'))
        return HttpResponseRedirect(reverse('themes_theme', kwargs={'name': theme['name']}))
    return render_to_response(request,
            'themes/home.html',
            {'themes':themes, 'previewing':previewing},
            )

def default_current_theme(func):
    """Decorator to ensure current theme for generic views."""
    def _wrapper(request, name=None, theme=None, **kwargs):
        if not theme:
            if name is not None:
                theme = get_object_or_404(Theme, name=name)
            elif getattr(request, 'site', None) and request.site['theme']:
                theme = request.site['theme']
            else:
                request.error(_('No theme to edit.'))
                return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
        return func(request, theme=theme, **kwargs)
    return _wrapper

#@permission_required('themes.change_theme')
@default_current_theme
def theme(request, theme, showing_menu=True):
    # Saves the theme to ensure all registered templates were created
    theme.create_templates()
    return render_to_response(request,
            'themes/theme.html',
            {'theme':theme, 'showing_menu':showing_menu},
            )

#@permission_required('themes.delete_theme')
@default_current_theme
def theme_delete(request, theme):
    # Templates first
    theme['templates'].delete()

    # Delete static files and their phisical files
    for sf in theme['static_files']:
        sf['file'].delete()
        sf.delete()

    name = theme['name']

    # Finally, deletes the theme
    theme.delete()

    request.info(_('Theme "%s" deleted.')%unicode(name))
    return HttpResponseRedirect(reverse('themes_home'))

#@permission_required('themes.change_theme')
@default_current_theme
def theme_rename(request, theme):
    if request.method == 'POST':
        # Sets a new verbose name and its slugified name
        theme['verbose_name'] = request.POST['name']
        new_name = slugify(theme['verbose_name'])
        counter = 0
        while Theme.query().filter(name=new_name).exclude(pk=theme['pk']).count():
            counter += 1
            new_name = '%s-%s'%(slugify(theme['verbose_name']), counter)
        theme['name'] = new_name
        theme.save()

        ret = {'new_url': reverse('themes_theme', kwargs={'name': theme['name']})}
    else:
        ret = {'result': 'error'}
    
    # Returns a JSON with new URL to redirect it
    return JsonResponse(ret)

#@permission_required('themes.add_theme')
@default_current_theme
def theme_save_as(request, theme):
    if request.method == 'POST':
        # Theme
        new_theme = Theme()
        new_theme['verbose_name'] = request.POST['name']
        new_name = slugify(new_theme['verbose_name'])
        counter = 0
        while Theme.query().filter(name=new_name).exclude(pk=theme['pk']).count():
            counter += 1
            new_name = '%s-%s'%(slugify(theme['verbose_name']), counter)
        new_theme['name'] = new_name
        new_theme.save()

        # Templates
        for tpl in theme['templates']:
            new_tpl, new = new_theme['templates'].get_or_create(name=tpl['name'])
            new_tpl['notes'] = tpl['notes']
            new_tpl['content'] = tpl['content']
            new_tpl['engine'] = tpl['engine']
            new_tpl.save()

        """
        # FIXME
        # Static files
        for sf in theme['static_files']:
            try:
                new_sf, new = new_theme['static_files'].get_or_create(name=sf['name'])
                new_sf.url = sf.url
                new_sf.mimetype = sf.mimetype
                new_sf.save()

                if sf.file:
                    # Finds a name for the new file
                    root = sf.file.path.replace(sf.file.name, '')
                    name, ext = os.path.splitext(sf.file.name)
                    while os.path.exists(root + name + ext):
                        name += '_'

                    # Reads the old file to make a ContentFile instance
                    fp = file(sf.file.path)
                    content = ContentFile(fp.read())
                    fp.close()
                    
                    # Saves the new file for the new static file object
                    new_sf.file.save(name+ext, content)
            except BaseException as e:
                print(sf, e.__class__, e)
                raise
        """
        ret = {'new_url': reverse('themes_theme', kwargs={'name': new_theme['name']})}
    else:
        ret = {'result': 'error'}
    
    return JsonResponse(ret)

#@permission_required('themes.set_default_theme')
@default_current_theme
def theme_set_default(request, theme):
    theme['is_default'] = True
    theme.save()
    request.info(_('Theme "%s" set as default.')%theme['name'])
    return HttpResponseRedirect(reverse('themes_theme', kwargs={'name':theme['name']}))

#@permission_required('themes.set_default_theme')
def theme_preview(request, name=None):
    if name:
        resp = HttpResponseRedirect('/')
        resp.set_cookie(app_settings.CURRENT_THEME_COOKIE, name)
        request.info(_('Theme "%s" set to preview.')%name)
    else:
        resp = HttpResponseRedirect(reverse('themes_home'))
        resp.delete_cookie(app_settings.CURRENT_THEME_COOKIE)
        request.info(_('Disabled the theme preview.'))
    return resp

#@csrf_exempt
#@permission_required('themes.change_theme')
@default_current_theme
def theme_up_file(request, theme):
    new_static_files = []

    if request.method == 'POST':
        db_field = ThemeStaticFile._meta.fields['file']
        for up_file in request.FILES.getlist('dragupload[]'):
            name = up_file.name
            while theme['static_files'].filter(name=name).count():
                name += '_'

            sf = ThemeStaticFile(theme=theme, name=name, mime_type=up_file.content_type)
            upload_name = db_field.generate_filename(sf, up_file.name)
            upload_name = db_field.storage.save(upload_name, up_file)
            sf['file'] = FieldFile(sf, db_field, upload_name)
            sf.save()

            new_static_files.append(sf)

        # Calls the signal after static files changed
        theme_static_files_changed.send(sender=request.site, theme=theme, request=request, items=new_static_files)

    return render_to_response(request,
            'themes/theme_up_file.html',
            {'theme': theme, 'new_static_files': new_static_files},
            )

#@csrf_exempt
#@permission_required('themes.change_theme')
@default_current_theme
def theme_edit_child(request, theme):
    if request.method == 'POST':
        if request.POST['type'] == 'template':
            item = theme['templates'].get(name=request.POST['name'])
            item['content'] = request.POST.get('content', '')
            item.save()
            return HttpResponse('ok')

        elif request.POST['type'] == 'static-file':
            item = theme['static_files'].get(name=request.POST['name'])
            file_path = item['file'].path
            fp = file(file_path, 'w')
            fp.write(request.POST.get('content', '').encode('utf-8'))
            fp.close()

            # Calls the signal after static files changed
            theme_static_files_changed.send(sender=request.site, theme=theme, request=request, items=[item])

            return HttpResponse('ok')

    else:
        rel = request.GET['rel']
        typ, pk = rel.rsplit('-',1)

        if typ == 'template':
            item = theme['templates'].get(pk=pk)
            content = item['content'] if item['content'] != None else ''
            return HttpResponse(u'type(html)'+content)
        elif typ in ('static-file', 'static-url'):
            item = theme['static_files'].get(pk=pk)
            ext = os.path.splitext(item['file'].name)[-1][1:]

            if item['mime_type'].startswith('text/'):
                try:
                    content = u'type(%s)%s'%(ext, item['file'].read().decode('utf-8'))
                    return HttpResponse(content)
                except ValueError:
                    pass

            try:
                url = item.get_url()
            except ValueError:
                url = item['url']

            ret = {'type':item.get_type(), 'url':url, 'mime_type':item['mime_type']}
            return JsonResponse(ret)

#@csrf_exempt
#@permission_required('themes.change_theme')
@default_current_theme
def theme_delete_child(request, theme):
    ret = {'result':'ok'}

    if request.method == 'POST':
        if request.POST['type'] == 'template':
            item = theme['templates'].get(name=request.POST['name'])
            ret['info'] = {'pk':str(item['pk']), 'name':item['name'], 'type':'template'}
            item.delete()

        elif request.POST['type'] in ('static-file','static-url'):
            item = theme['static_files'].get(name=request.POST['name'])
            ret['info'] = {'pk':str(item['pk']), 'name':item['name'], 'type':request.POST['type']}
            item.delete()

            # Calls the signal after static files changed
            if request.POST['type'] == 'static-file':
                theme_static_files_deleted.send(sender=request.site, theme=theme, request=request, items=[item])

    return JsonResponse(ret)

#@csrf_exempt
#@permission_required('themes.add_themetemplate')
@default_current_theme
def theme_create_template(request, theme):
    ret = {}

    if request.method == 'POST':
        name = request.POST['name']
        if theme['templates'].filter(name=name).count():
            ret = {'result':'error', 'message':'Template already exists.'}
        else:
            tpl = theme['templates'].create(name=name)
            ret = {'result':'ok', 'info':{'pk':str(tpl['pk'])}}

    return JsonResponse(ret)

#@csrf_exempt
#@permission_required('themes.add_themestaticfile')
@default_current_theme
def theme_create_static_file(request, theme):
    ret = {}

    if request.method == 'POST':
        name = request.POST['name']
        if theme['static_files'].filter(name=name).count():
            ret = {'result':'error', 'message':'Static File already exists.'}
        else:
            sf = theme['static_files'].create(name=name)

            if request.POST.get('url', None):
                sf['url'] = request.POST['url']
                sf['mime_type'] = mimetypes.guess_type(sf['url'])[0] or ''
                sf.save()
            else:
                # Saves an empty file as a starting point
                content_file = ContentFile('')
                db_field = ThemeStaticFile._meta.fields['file']
                file_name = '%s-%s-%s'%(theme['pk'], sf['pk'], name)
                upload_name = db_field.generate_filename(sf, file_name)
                upload_name = db_field.storage.save(upload_name, content_file)
                sf['file'] = FieldFile(sf, db_field, upload_name)

                # Detects the mime_type for the given name
                sf['mime_type'] = mimetypes.guess_type(file_name)[0] or ''
                sf.save()

                # Calls the signal after static files changed
                theme_static_files_changed.send(sender=request.site, theme=theme, request=request, items=[sf])

            ret = {'result':'ok', 'info':{'pk':str(sf['pk']), 'url':sf.get_url()}}

    return JsonResponse(ret)

#@permission_required('themes.download_theme')
@default_current_theme
def theme_download(request, theme):
    # Uses zipfile library to export the theme files as just one file
    zipf_path = export_theme(theme)
    fp = file(zipf_path)
    content = fp.read()
    fp.close()

    # Forces the download
    resp = HttpResponse(content, mime_type='application/zip')
    resp['Content-Disposition'] = 'attachment; filename=theme-%s.zip'%theme['name']
    return resp

#@permission_required('themes.import_theme')
def theme_import(request):
    if request.method == 'POST':
        try:
            # Calls the theme importing function to save theme, templates and static files in the right places
            theme = import_theme(request.FILES['file'])

            # Calls the signal after static files changed
            theme_static_files_changed.send(sender=request.site, theme=theme, request=request,
                    items=list(theme['static_files'].exclude(file=None)))

            # Final message and redirecting
            request.info(_('File imported with success!'))
            url_redirect = reverse('themes_theme', kwargs={'name': theme['name']})
        except ValueError as e:
            request.info(e)
            url_redirect = reverse('themes_home')
    return HttpResponseRedirect(url_redirect)

#@csrf_exempt
#@permission_required('themes.change_theme')
@default_current_theme
@render_template('themes/theme_upload.html')
def theme_upload(request, theme):
    if request.method == 'POST':
        up_file = request.FILES.getlist('dragupload[]')[0]
        try:
            import_theme(up_file, theme=theme)

            # Calls the signal after static files changed
            theme_static_files_changed.send(sender=request.site, theme=theme, request=request,
                    items=list(theme['static_files'].exclude(file=None)))

            request.info(_('File imported with success!'))
        except ValueError as e:
            request.info(e)
        return {'theme':theme, 'uploaded':True}
    else:
        return {'theme':theme}

def choose_theme(request):
    """
    Function used by setting THEMES_THEME_CHOOSING to get the current theme by the middleware.
    This function is simple but supports returning the default theme or the one set by a cookie,
    used by "Preview" function. But a similar function can be made to do more than that.
    """
    # Check first about a cookie with current theme
    if request.COOKIES.get(app_settings.CURRENT_THEME_COOKIE, None):
        try:
            return Theme.query().get(name=request.COOKIES[app_settings.CURRENT_THEME_COOKIE].value)
        except Theme.DoesNotExist:
            pass

    # Returns the default theme
    try:
        return Theme.query().get(is_default=True)
    except Theme.DoesNotExist:
        return None


