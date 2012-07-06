import zipfile
import os
import random
import shutil
import glob

try:
    import json as simplejson
except ImportError:
    import simplejson

from london.utils.translation import ugettext as _
from london.core.files.base import ContentFile
from london.db.models.fields.files import FieldFile

from models import Theme, ThemeStaticFile

def dump_file_name(sf):
    try:
        return os.path.split(sf['file'].name)[-1]
    except (AttributeError, ValueError):
        return None

def export_theme(theme):
    """
    Outputs a zipfile with the theme, its templates and static files.
    """
    dir_name = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for n in range(20)])
    work_dir = os.path.join('/tmp/', dir_name)
    os.makedirs(work_dir)
    os.chdir(work_dir)

    zipf_path = os.path.join(work_dir, 'theme-%s.zip'%theme['name'])
    zipf = zipfile.ZipFile(zipf_path, 'w')

    json = {
        'name': theme['name'],
        'verbose_name': theme['verbose_name'],
        'templates': [{
            'name': tpl['name'],
            'notes': tpl['notes'],
            'content': tpl['content'],
            'engine': tpl['engine'],
            } for tpl in theme['templates']],
        'static_files': [{
            'name': sf['name'],
            'url': sf['url'],
            'file': dump_file_name(sf),
            'mime_type': sf['mime_type'],
            } for sf in theme['static_files']],
        }
    jsonf_path = 'details.json'
    json_fp = file(jsonf_path, 'w')
    json_fp.write(simplejson.dumps(json))
    json_fp.close()

    zipf.write(jsonf_path)

    for sf in theme['static_files'].exclude(file__isnull=True).exclude(file=''):
        try:
            f_name = dump_file_name(sf)
            shutil.copyfile(sf['file'].path, os.path.join(work_dir, f_name))
            zipf.write(f_name)
        except ValueError:
            pass

    zipf.close()

    return zipf_path

def import_theme(zipfp, theme=None):
    """
    If a theme is informed, it assumes and theme imported fields are ignored
    """
    # Initializes the working area
    dir_name = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for n in range(20)])
    work_dir = os.path.join('/tmp/', dir_name)
    os.makedirs(work_dir)
    os.chdir(work_dir)

    # Opens and extracts the zip file
    zipf = zipfile.ZipFile(zipfp)
    zipf.extractall()

    # Loads driver JSON file
    json_fp = file('details.json')
    json = simplejson.loads(json_fp.read())
    json_fp.close()

    # Doesn't allow import existing theme (must delete before)
    if not theme and Theme.query().filter(name=json['name']).count():
        raise ValueError(_('Theme "%s" already exists.')%json['name'])

    # Creates the new theme
    if not theme:
        theme = Theme.query().create(name=json['name'], verbose_name=json['verbose_name'])

    # Creates the new templates
    for json_tpl in json['templates']:
        tpl, new = theme['templates'].get_or_create(name=json_tpl['name'])
        tpl['content'] = json_tpl['content']
        tpl['notes'] = json_tpl['notes']
        tpl['engine'] = json_tpl['engine']
        tpl.save()

    # Creates the new static files
    db_field = ThemeStaticFile._meta.fields['file']
    for json_sf in json['static_files']:
        sf, new = theme['static_files'].get_or_create(
                name=json_sf['name'],
                defaults={
                    'url': json_sf['url'],
                    'mime_type': json_sf['mime_type'],
                    },
                )

        if json_sf['file']:
            fp = file(json_sf['file'])
            content = ContentFile(fp.read())
            fp.close()

            upload_name = db_field.generate_filename(sf, json_sf['file'])
            upload_name = db_field.storage.save(upload_name, content)
            sf['file'] = FieldFile(sf, db_field, upload_name)
            sf.save()

    return theme

