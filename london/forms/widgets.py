"""
Some widgets were copied from Django 1.4 and modified to adapt to London's way of working.
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import datetime
import copy
import re
from itertools import chain

from london.utils.safestring import mark_safe
from london.utils import datetime_safe, formats
from london.utils.translation import ugettext_lazy
from london.http import QueryDict
from london.utils.html import escape, conditional_escape
from london.utils.encoding import StrAndUnicode, force_unicode



MEDIA_TYPES = ('css','js')

class Media(StrAndUnicode):
    def __init__(self, media=None, **kwargs):
        if media:
            media_attrs = media.__dict__
        else:
            media_attrs = kwargs

        self._css = {}
        self._js = []

        for name in MEDIA_TYPES:
            getattr(self, 'add_' + name)(media_attrs.get(name, None))

        # Any leftover attributes must be invalid.
        # if media_attrs != {}:
        #     raise TypeError("'class Media' has invalid attribute(s): %s" % ','.join(media_attrs.keys()))

    def __unicode__(self):
        return self.render()

    def render(self):
        return mark_safe(u'\n'.join(chain(*[getattr(self, 'render_' + name)() for name in MEDIA_TYPES])))

    def render_js(self):
        return [u'<script type="text/javascript" src="/ajax/%s"></script>' % path for path in self._js]

    def render_css(self):
        # To keep rendering order consistent, we can't just iterate over items().
        # We need to sort the keys, and iterate over the sorted list.
        media = self._css.keys()
        media.sort()
        return chain(*[
            [u'<link href="/ajax/%s" type="text/css" media="%s" rel="stylesheet" />' % (path, medium)
                    for path in self._css[medium]]
                for medium in media])

    def __getitem__(self, name):
        "Returns a Media object that only contains media of the given type"
        if name in MEDIA_TYPES:
            return Media(**{str(name): getattr(self, '_' + name)})
        raise KeyError('Unknown media type "%s"' % name)

    def add_js(self, data):
        if data:
            for path in data:
                if path not in self._js:
                    self._js.append(path)

    def add_css(self, data):
        if data:
            for medium, paths in data.items():
                for path in paths:
                    if not self._css.get(medium) or path not in self._css[medium]:
                        self._css.setdefault(medium, []).append(path)

    def __add__(self, other):
        combined = Media()
        for name in MEDIA_TYPES:
            getattr(combined, 'add_' + name)(getattr(self, '_' + name, None))
            getattr(combined, 'add_' + name)(getattr(other, '_' + name, None))
        return combined

def media_property(cls):
    def _media(self):
        # Get the media property of the superclass, if it exists
        if hasattr(super(cls, self), 'media'):
            base = super(cls, self).media
        else:
            base = Media()

        # Get the media definition for this class
        definition = getattr(cls, 'Media', None)
        if definition:
            extend = getattr(definition, 'extend', True)
            if extend:
                if extend == True:
                    m = base
                else:
                    m = Media()
                    for medium in extend:
                        m = m + base[medium]
                return m + Media(definition)
            else:
                return Media(definition)
        else:
            return base
    return property(_media)

class MediaDefiningClass(type):
    "Metaclass for classes that can have media definitions"
    def __new__(cls, name, bases, attrs):
        new_class = super(MediaDefiningClass, cls).__new__(cls, name, bases,
                                                           attrs)
        if 'media' not in attrs:
            new_class.media = media_property(new_class)
        return new_class

class Widget(object):
    __metaclass__ = MediaDefiningClass
    readonly = False
    attrs = None
    is_localized = False
    is_required = False

    def __init__(self, attrs=None):
        self.attrs = attrs or {}

    def render_label(self, name, label):
        return mark_safe(u'<label for="%s">%s:</label>'%(self.attrs.get('id', name), label))

    def value_from_datadict(self, data, files, name):
        """This method is called before any kind of validation nor cleaning, just to return a raw
        value for that."""
        return data.get(name, None)

    def render_errors(self, name, errors):
        if not errors:
            return ''
        return mark_safe(unicode(errors))

    def render_help_box(self, name, help_text):
        if not help_text:
            return ''
        return mark_safe(u'<span class="help_text" for="%s">%s</span>'%(self.attrs.get('id', name), help_text))

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        attrs = dict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        if self.attrs is not None:
            obj.attrs = self.attrs.copy()
        return obj


class Input(Widget):
    input_type = None

    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        if self.attrs:
            attrs.update(self.attrs)
        attrs['name'] = name
        
        # FIXME: maybe this should be moved with an opposite way to CheckboxInput
        if self.input_type != 'checkbox':
            attrs['value'] = self._format_value(value) if value is not None else ''
        
        attrs.setdefault('id', 'id_'+name)
        if self.readonly:
            attrs.setdefault('readonly', 'readonly')

        if self.input_type:
            attrs['type'] = self.input_type

        self.attrs.update(attrs) # XXX from the MERGE
        return mark_safe(u'<input %s/>'%' '.join(['%s="%s"'%(key,value) for key,value in attrs.items()]))

    def _format_value(self, value):
        if self.is_localized:
            return formats.localize_input(value)
        return value


class TextInput(Input):
    input_type = 'text'


class ColorInput(Input):
    input_type = 'color'


class EmailInput(Input):
    input_type = 'email'


class NumberInput(Input):
    #input_type = 'number'
    input_type = 'text'


class HiddenInput(Input):
    input_type = 'hidden'

    def render_label(self, name, label):
        return ''

    def render_errors(self, name, errors):
        return ''

    def render_help_box(self, name, help_text):
        return ''


class CheckboxInput(Input):
    input_type = 'checkbox'

    def render(self, name, value, attrs=None):
        attrs = attrs or {}

        if value in (True,'on'):
            attrs['checked'] = 'checked'

        return super(CheckboxInput, self).render(name, value in (True,'on'), attrs)

    def value_from_datadict(self, data, files, name):
        try:
            value = data[name]
        except KeyError:
            return False

        if isinstance(value, bool):
            return value

        return value.lower() == 'on'


class Textarea(Widget):
    def render(self, name, value, attrs=None):
        self.attrs = attrs or {}
        self.attrs['name'] = name
        self.attrs.setdefault('id', 'id_'+name)

        return mark_safe(u'<textarea %(attrs)s>%(value)s</textarea>'%{
                'attrs': ' '.join(['%s="%s"'%(k,v) for k,v in self.attrs.items()]),
                'value': value or '',
                })


class PasswordInput(Input):
    input_type = 'password'
    render_value = False

    def render(self, name, value, attrs=None):
        if not self.render_value:
            value = ''
        else:
            value = unicode(value)

        return super(PasswordInput, self).render(name, value, attrs)


class Select(Widget):
    choices = None

    def __init__(self, choices=None, **kwargs):
        self.choices = choices or []
        super(Select, self).__init__(**kwargs)

    def render(self, name, value, attrs=None):
        self.attrs = attrs or {}
        self.attrs['name'] = name
        self.attrs.setdefault('id', 'id_'+name)

        options = [u'<option value="%s"%s>%s</option>'%(k, self.get_selected(value, k), v)
                for k,v in self.choices]

        return mark_safe(u'<select %(attrs)s>%(options)s</select>'%{
                'attrs': ' '.join(['%s="%s"'%(k,v) for k,v in self.attrs.items()]),
                'options': ''.join(options),
                })

    def get_selected(self, value, key):
        return ' selected="selected"' if value == key else ''

    def value_from_datadict(self, data, files, name):
        return data.get(name, None)

    def __deepcopy__(self, memo):
        obj = super(Select, self).__deepcopy__(memo)
        obj.choices = copy.deepcopy(self.choices)
        return obj


class SelectMultiple(Select):
    allow_multiple_selected = True

    def render(self, name, value, attrs=None):
        self.attrs = attrs or {}
        self.attrs['name'] = name
        self.attrs['multiple'] = 'multiple'
        self.attrs.setdefault('id', 'id_'+name)

        options = [u'<option value="%s"%s>%s</option>'%(k, self.get_selected(value, k), v)
                for k,v in self.choices]

        return mark_safe(u'<select %(attrs)s>%(options)s</select>'%{
                'attrs': ' '.join(['%s="%s"'%(k,v) for k,v in self.attrs.items()]),
                'options': ''.join(options),
                })

    def value_from_datadict(self, data, files, name):
        if isinstance(data, QueryDict):
            return data.getlist(name)
        return data.get(name, None)

    def get_selected(self, value, key):
        return ' selected="selected"' if key in value else ''

    """ TODO
    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        initial_set = set([force_unicode(value) for value in initial])
        data_set = set([force_unicode(value) for value in data])
        return data_set != initial_set
    """


class CheckboxSelectMultiple(SelectMultiple):
    def render(self, name, value, attrs=None):
        self.attrs = attrs or {}
        self.attrs.setdefault('id', 'id_'+name)

        options = []
        for pk,display in self.choices:
            item_attrs = self.get_item_attrs(pk, display)
            options.append(
                u'<li><input type="checkbox" name="%(name)s[%(pk)s]" value="%(pk)s" id="%(id)s" %(sel)s %(attrs)s /> <label for="%(id)s">%(display)s</label></li>'%{
                    'name': name,
                    'pk': pk,
                    'id': 'id_%s_%s'%(name,pk),
                    'sel': self.get_selected(value, pk),
                    'display': display,
                    'attrs': ' '.join(['%s="%s"'%(k,v) for k,v in item_attrs.items()]),
                    })

        return mark_safe(u'<ul %(attrs)s>%(options)s</ul>'%{
                'attrs': ' '.join(['%s="%s"'%(k,v) for k,v in self.attrs.items()]),
                'options': ''.join(options),
                })

    def get_item_attrs(self, pk, display):
        return {}

    def get_selected(self, value, key):
        if not value:
            return ''
        return ' checked="checked"' if key in value else ''
    
    def value_from_datadict(self, data, files, name):
        result = ()
        re_pattern = re.compile(r'^%s\[(.*)\]$' % name)
        for data_item in data:
            match = re_pattern.match(data_item)
            if match:
                key = "%s[%s]" % (name, match.groups()[0])
                if data[key] == 'on':
                    result += match.groups()
        return result


class MultiWidget(Widget):
    def __init__(self, widgets, attrs=None):
        self.widgets = [isinstance(w, type) and w() or w for w in widgets]
        super(MultiWidget, self).__init__(attrs)

    def render_in_separate(self, name, value, attrs=None):
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))

        return output
    
    @property
    def media(self):
        "Media for a multiwidget is the combination of all media of the subwidgets"
        media = Media()
        for w in self.widgets:
            media = media + w.media
        return media

    def render(self, name, value, attrs=None):
        output = self.render_in_separate(name, value, attrs)
        return mark_safe(self.format_output(output))

    def format_output(self, rendered_widgets):
        return u''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        return [widget.value_from_datadict(data, files, name + '_%s' % i) for i, widget in enumerate(self.widgets)]

    def __deepcopy__(self, memo):
        obj = super(MultiWidget, self).__deepcopy__(memo)
        obj.widgets = copy.deepcopy(self.widgets)
        return obj


class MonthYearSelect(MultiWidget):
    def __init__(self, years_from_now=10, attrs=None):
        today = datetime.date.today()

        months = [('', '---')] + [(num, '%02d'%num) for num in range(1,13)]

        if years_from_now > 0:
            year_range = range(today.year, today.year+years_from_now)
        else:
            year_range = range(today.year+years_from_now, today.year+1)
        years = [('', '---')] + [(num, str(num)) for num in year_range]

        widgets = [
                Select(choices=months, attrs={'class':'float-left'}),
                Select(choices=years, attrs={'class':'float-left'}),
                ]

        super(MonthYearSelect, self).__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, basestring):
            return map(int, value.split('/')) if value else ['','']
        elif value is None:
            return None, None
        else:
            return value

    def value_from_datadict(self, data, files, name):
        values = super(MonthYearSelect, self).value_from_datadict(data, files, name)

        if all(values):
            return map(int, values)
        else:
            return None, None

class DateInput(Input):
    #input_type = 'date'
    input_type = 'text'

    def __init__(self, attrs=None, format=None):
        attrs = attrs or {}
        attrs.setdefault('maxlength',10)
        super(DateInput, self).__init__(attrs)
        if format:
            self.format = format
            self.manual_format = True
        else:
            self.format = formats.get_format('DATE_INPUT_FORMATS')[0]
            self.manual_format = False

    def _format_value(self, value):
        if self.is_localized and not self.manual_format:
            return formats.localize_input(value)
        elif hasattr(value, 'strftime'):
            value = datetime_safe.new_date(value)
            return value.strftime(self.format)
        return value

    def _has_changed(self, initial, data):
        # If our field has show_hidden_initial=True, initial will be a string
        # formatted by HiddenInput using formats.localize_input, which is not
        # necessarily the format used for this widget. Attempt to convert it.
        try:
            input_format = formats.get_format('DATE_INPUT_FORMATS')[0]
            initial = datetime.datetime.strptime(initial, input_format).date()
        except (TypeError, ValueError):
            pass
        return super(DateInput, self)._has_changed(self._format_value(initial), data)

class DateTimeInput(Input):
    #input_type = 'datetime'
    input_type = 'text'

    def __init__(self, attrs=None, format=None):
        super(DateTimeInput, self).__init__(attrs)
        if format:
            self.format = format
            self.manual_format = True
        else:
            self.format = formats.get_format('DATETIME_INPUT_FORMATS')[0]
            self.manual_format = False

    def _format_value(self, value):
        if self.is_localized and not self.manual_format:
            return formats.localize_input(value)
        elif hasattr(value, 'strftime'):
            value = datetime_safe.new_datetime(value)
            return value.strftime(self.format)
        return value

    def _has_changed(self, initial, data):
        # If our field has show_hidden_initial=True, initial will be a string
        # formatted by HiddenInput using formats.localize_input, which is not
        # necessarily the format used for this widget. Attempt to convert it.
        try:
            input_format = formats.get_format('DATETIME_INPUT_FORMATS')[0]
            initial = datetime.datetime.strptime(initial, input_format)
        except (TypeError, ValueError):
            pass
        return super(DateTimeInput, self)._has_changed(self._format_value(initial), data)


class TimeInput(Input):
    #input_type = 'time'
    input_type = 'text'

    def __init__(self, attrs=None, format=None):
        attrs = attrs or {}
        attrs.setdefault('maxlength',8)
        super(TimeInput, self).__init__(attrs)
        if format:
            self.format = format
            self.manual_format = True
        else:
            self.format = formats.get_format('TIME_INPUT_FORMATS')[0]
            self.manual_format = False

    def _format_value(self, value):
        if self.is_localized and not self.manual_format:
            return formats.localize_input(value)
        elif hasattr(value, 'strftime'):
            return value.strftime(self.format)
        return value

    def _has_changed(self, initial, data):
        # If our field has show_hidden_initial=True, initial will be a string
        # formatted by HiddenInput using formats.localize_input, which is not
        # necessarily the format used for this  widget. Attempt to convert it.
        try:
            input_format = formats.get_format('TIME_INPUT_FORMATS')[0]
            initial = datetime.datetime.strptime(initial, input_format).time()
        except (TypeError, ValueError):
            pass
        return super(TimeInput, self)._has_changed(self._format_value(initial), data)


class SplitDateTimeWidget(MultiWidget):
    """
    A Widget that splits datetime input into two <input type="text"> boxes.
    """

    def __init__(self, attrs=None, date_format=None, time_format=None):
        widgets = (DateInput(attrs=attrs, format=date_format),
                   TimeInput(attrs=attrs, format=time_format))
        super(SplitDateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]


class FileInput(Input):
    input_type = 'file'
    needs_multipart_form = True

    def render(self, name, value, attrs=None):
        return super(FileInput, self).render(name, None, attrs=attrs)

    def value_from_datadict(self, data, files, name):
        "File widgets take data from FILES, not POST"
        return files.get(name, None)

    def _has_changed(self, initial, data):
        if data is None:
            return False
        return True


FILE_INPUT_CONTRADICTION = object()

class ClearableFileInput(FileInput):
    initial_text = ugettext_lazy('Currently')
    input_text = ugettext_lazy('Change')
    clear_checkbox_label = ugettext_lazy('Clear')

    template_with_initial = u'%(initial_text)s: %(initial)s %(clear_template)s<br />%(input_text)s: %(input)s'

    template_with_clear = u'%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'

    def clear_checkbox_name(self, name):
        """
        Given the name of the file input, return the name of the clear checkbox
        input.
        """
        return name + '-clear'

    def clear_checkbox_id(self, name):
        """
        Given the name of the clear checkbox input, return the HTML id for it.
        """
        return name + '_id'

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = u'%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = (u'<a href="%s" rel="nohistory">%s</a>'
                                        % (escape(value.url), escape(force_unicode(value))))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)

    def value_from_datadict(self, data, files, name):
        upload = super(ClearableFileInput, self).value_from_datadict(data, files, name)
        if not self.is_required and CheckboxInput().value_from_datadict(
            data, files, self.clear_checkbox_name(name)):
            if upload:
                # If the user contradicts themselves (uploads a new file AND
                # checks the "clear" checkbox), we return a unique marker
                # object that FileField will turn into a ValidationError.
                return FILE_INPUT_CONTRADICTION
            # False signals to clear any existing value, as opposed to just None
            return False
        return upload


class StaticAutoCompleteWidget(TextInput):
    accept_not_found = False

    def __init__(self, *args, **kwargs):
        self.choices = [(unicode(k), unicode(v)) for k,v in kwargs.pop('choices', [])]
        self.accept_not_found = kwargs.pop('accept_not_found', False)

        super(StaticAutoCompleteWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        value = unicode(value or '')
        choices_dict = dict([(unicode(k), unicode(v)) for k,v in self.choices if k])
        attrs = attrs or {}
        attrs['autocomplete'] = 'off'

        if self.accept_not_found:
            attrs['class'] = attrs.get('class', '') + ' accept-not-found'

        ret = super(StaticAutoCompleteWidget, self).render('_'+name, choices_dict.get(value, value), attrs)
        options = '<ul class="static-auto-complete-options">%(options)s</ul>'%{
                'options': ''.join(['<li class="auto-complete-option" rel="%s"><a href="javascript:void(0)">%s</a></li>'%(k,v) for k,v in self.choices if k not in ('',None)]),
                }
        hidden = '<input type="hidden" name="%s" value="%s"/>'%(name, value or '')
        return mark_safe('<span class="static-auto-complete-container">%s %s %s</span>'%(ret, options, hidden))


class ListByCommasTextInput(TextInput):
    """Widget similar to TextInput but shows a string list separated by commas.
    FIXME / from the MERGE: to be removed"""

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None) or ''
        return [item.strip() for item in value.split(',') if item.strip()]

    def render(self, name, value, attrs=None):
        value = ', '.join(value) if value else ''
        return super(ListByCommasTextInput, self).render(name, value, attrs)


class ListByCommaInput(TextInput):
    def value_from_datadict(self, data, files, name):
        value = super(ListByCommaInput, self).value_from_datadict(data, files, name)
        value = value or ''
        return [i.strip() for i in value.split(',') if i.strip()]

    def _format_value(self, value):
        value = value or []
        return ', '.join(value)


