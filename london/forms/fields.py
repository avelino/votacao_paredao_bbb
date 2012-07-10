"""
The class attribute "creation_counter" idea was partially copied from Django 1.4
Copyright (c) Django Software Foundation and individual contributors. All rights reserved.
"""
import datetime
import re
import copy

from london.utils.strings import make_title
from london.forms.widgets import Widget, TextInput, HiddenInput, CheckboxInput, Textarea, PasswordInput
from london.forms.widgets import Select, DateInput, TimeInput, DateTimeInput, EmailInput, NumberInput
from london.forms.widgets import ClearableFileInput, FILE_INPUT_CONTRADICTION
from london.exceptions import ValidationError, IgnoreField
from london.utils.translation import ugettext as _
from london.utils.formats import sanitize_separators
from london.utils.safestring import mark_safe


class Field(object):
    required = True
    initial = None
    verbose_name = None
    widget = TextInput
    _label = None
    readonly = False
    help_text = ''
    is_file_field = False
    returns_initial = True
    attrs = None
    required_message = None

    # This class attribute increments each time a field is created to keep the right field order
    creation_counter = 0

    def __init__(self, **kwargs):
        self.required = kwargs.get('required', self.required)
        self.initial = kwargs.get('initial', self.initial)
        self.verbose_name = kwargs.get('verbose_name', self.verbose_name)
        self.widget = kwargs.get('widget', self.widget)
        self._label = kwargs.get('label', self._label)
        self.help_text = kwargs.get('help_text', self.help_text)
        self.name = kwargs.get('name', None)
        self.required_message = kwargs.get('required_message', None)
        self.attrs = kwargs.get('attrs', {})

        # Increments creation counter to make possible to sort fields by creation order
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def get_label(self):
        return self._label or make_title(self.name)
    def set_label(self, label):
        self._label = label
    label = property(get_label, set_label)

    def clean(self, value):
        """This method is called after widget's value_from_data_dict with a raw value just to clean and validate"""
        if self.required and not value:
            msg = self.required_message or 'Field "%s" is required.' % self.label
            raise ValidationError(msg)

        return value

    def get_widget(self, form):
        widget = self.widget if isinstance(self.widget, Widget) else self.widget()
        widget.is_required = self.required

        widget_attrs = {}
        widget_attrs.update(self.attrs)
        widget_attrs.update(widget.attrs or {})
        widget.attrs = widget_attrs

        return widget

    def prepare_value(self, value):
        """Prepare the given value to be rendered for the form."""
        return value

    def render_widget(self, form=None, name=None, value=None, attrs=None):
        name = name or self.name
        value = value or self.initial
        widget = self.get_widget(form)
        return widget.render(name=name, value=value, attrs=attrs)

    def __unicode__(self):
        return self.render_widget()

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        if self.attrs is not None:
            obj.attrs = self.attrs.copy()
        obj.widget = copy.copy(self.widget) if isinstance(self.widget, Widget) else self.widget
        return obj

    def get_verbose_name(self):
        return self.verbose_name or self.name.replace('_',' ').capitalize()


class CharField(Field):
    max_length = None
    force_lower_case = False
    force_upper_case = False
    force_capitalized = False

    def __init__(self, **kwargs):
        self.max_length = kwargs.pop('max_length', self.max_length)
        self.force_lower_case = kwargs.pop('force_lower_case', self.force_lower_case)
        self.force_upper_case = kwargs.pop('force_upper_case', self.force_upper_case)
        self.force_capitalized = kwargs.pop('force_capitalized', self.force_capitalized)

        if self.force_lower_case + self.force_upper_case + self.force_capitalized > 1:
            raise SyntaxError('A CharField can have only one of attributes "force_lower_case", "force_upper_case" and "force_capitalized" set as True.')

        super(CharField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(CharField, self).clean(value)
        if isinstance(value, basestring) and value:
            if self.force_lower_case:
                value = value.lower()
            elif self.force_upper_case:
                value = value.upper()
            elif self.force_capitalized:
                value = value[0].upper() + value[1:]

        return value or ''


class DecimalField(Field):
    max_digits = None
    decimal_places = None

    def __init__(self, **kwargs):
        self.max_digits = kwargs.pop('max_digits', self.max_digits)
        self.decimal_places = kwargs.pop('decimal_places', self.decimal_places)
        super(DecimalField, self).__init__(**kwargs)

        self.attrs.setdefault('class','')
        self.attrs['class'] += ' decimal_field'

    def clean(self, value):
        value = super(DecimalField, self).clean(value)
        return sanitize_separators(value) or None


class MoneyField(Field):
    def __init__(self, **kwargs):
        super(MoneyField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' money_field'

    def clean(self, value):
        value = super(MoneyField, self).clean(value)
        return sanitize_separators(value) or None


class FileField(Field):
    widget = ClearableFileInput
    default_error_messages = {
        'invalid': _(u"No file was submitted. Check the encoding type on the form."),
        'missing': _(u"No file was submitted."),
        'empty': _(u"The submitted file is empty."),
        'max_length': _(u'Ensure this filename has at most %(max)d characters (it has %(length)d).'),
        'contradiction': _(u'Please either submit a file or check the clear checkbox, not both.')
    }
    is_file_field = True
    returns_initial = False

    def __init__(self, *args, **kwargs):
        self.max_length = kwargs.pop('max_length', None)
        self.allow_empty_file = kwargs.pop('allow_empty_file', False)
        super(FileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        if data in validators.EMPTY_VALUES:
            return None

        # UploadedFile objects should have name and size attributes.
        try:
            file_name = data.name
            file_size = data.size
        except AttributeError:
            raise ValidationError(self.error_messages['invalid'])

        if self.max_length is not None and len(file_name) > self.max_length:
            error_values =  {'max': self.max_length, 'length': len(file_name)}
            raise ValidationError(self.error_messages['max_length'] % error_values)
        if not file_name:
            raise ValidationError(self.error_messages['invalid'])
        if not self.allow_empty_file and not file_size:
            raise ValidationError(self.error_messages['empty'])

        return data

    def clean(self, data, initial=None):
        # If the widget got contradictory inputs, we raise a validation error
        if data is FILE_INPUT_CONTRADICTION:
            raise ValidationError(self.error_messages['contradiction'])
        # False means the field value should be cleared; further validation is
        # not needed.
        if data is False:
            if not self.required:
                return False
            # If the field is required, clearing is not possible (the widget
            # shouldn't return False data in that case anyway). False is not
            # in validators.EMPTY_VALUES; if a False value makes it this far
            # it should be validated from here on out as None (so it will be
            # caught by the required check).
            data = None
        if not data and initial:
            return initial
        return super(FileField, self).clean(data)

    def bound_data(self, data, initial):
        if data in (None, FILE_INPUT_CONTRADICTION):
            return initial
        return data


class ImageField(FileField):
    default_error_messages = {
        'invalid_image': _(u"Upload a valid image. The file you uploaded was either not an image or a corrupted image."),
    }

    def to_python(self, data):
        """
        Checks that the file-upload field data contains a valid image (GIF, JPG,
        PNG, possibly others -- whatever the Python Imaging Library supports).
        """
        f = super(ImageField, self).to_python(data)
        if f is None:
            return None

        # Try to import PIL in either of the two ways it can end up installed.
        try:
            from PIL import Image
        except ImportError:
            import Image

        # We need to get a file object for PIL. We might have a path or we might
        # have to read the data into memory.
        if hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file = StringIO(data.read())
            else:
                file = StringIO(data['content'])

        try:
            # load() is the only method that can spot a truncated JPEG,
            #  but it cannot be called sanely after verify()
            trial_image = Image.open(file)
            trial_image.load()

            # Since we're about to use the file again we have to reset the
            # file object if possible.
            if hasattr(file, 'reset'):
                file.reset()

            # verify() is the only method that can spot a corrupt PNG,
            #  but it must be called immediately after the constructor
            trial_image = Image.open(file)
            trial_image.verify()
        except ImportError:
            # Under PyPy, it is possible to import PIL. However, the underlying
            # _imaging C module isn't available, so an ImportError will be
            # raised. Catch and re-raise.
            raise
        except Exception: # Python Imaging Library doesn't recognize it as an image
            raise ValidationError(self.error_messages['invalid_image'])
        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f


class TextField(Field):
    widget = Textarea


class BooleanField(Field):
    widget = CheckboxInput


class PasswordField(CharField):
    max_length = 50
    widget = PasswordInput
    returns_initial = False

    def clean(self, value):
        if not value:
            raise IgnoreField('Value "%s" is not a valid password'%value)
        return value


class EmailField(CharField):
    max_length = 100
    widget = EmailInput

    def __init__(self, **kwargs):
        super(EmailField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' email_field'


class IntegerField(Field):
    widget = NumberInput

    def __init__(self, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' integer_field'

    def clean(self, value):
        value = super(IntegerField, self).clean(value)
        if value is None or value == '':
            return None

        try:
            return int(value)
        except ValueError:
            raise ValidationError('Invalid integer value.')


class FloatField(Field):
    widget = TextInput

    def __init__(self, **kwargs):
        super(FloatField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' float_field'

    def clean(self, value):
        value = super(FloatField, self).clean(value)
        try:
            return float(value)
        except ValueError:
            raise ValidationError('Invalid float value.')


class ChoiceField(Field):
    choices = None
    widget = Select
    empty_string = '---'

    def __init__(self, **kwargs):
        self.choices = kwargs.pop('choices', [])
        super(ChoiceField, self).__init__(**kwargs)

    def get_choices(self):
        choices = list(self.choices)
        if not self.required and len([c for c in choices if not c[0]]) == 0:
            choices.insert(0, ('', self.empty_string))

        # Parses the list transforming single items in pairs
        choices = [(c if isinstance(c, (list,tuple)) else (c,c)) for c in choices]

        return choices

    def get_widget(self, form):
        widget = self.widget if isinstance(self.widget, Widget) else self.widget()
        widget.choices = self.get_choices()
        return widget

    def __deepcopy__(self, memo):
        obj = super(ChoiceField, self).__deepcopy__(memo)
        obj.choices = copy.deepcopy(self.choices)
        return obj


class DateField(Field):
    widget = DateInput
    WEEK_DAYS = {
            'monday':0,
            'mon':0,
            'tuesday':1,
            'tues':1,
            'wednesday':2,
            'weds':2,
            'thursday':3,
            'thurs':3,
            'friday':4,
            'fri':4,
            'saturday':5,
            'sat':5,
            'sunday':6,
            'sun':6,
            }

    def __init__(self, **kwargs):
        super(DateField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' date_field'

    def convert_from_multiple_formats(self, value, formats):
        for fmt in formats:
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except ValueError:
                pass

    def clean(self, value):
        value = super(DateField, self).clean(value)

        # FIXME: this method shouldn't be here and the datetime formats below as well (they should be in the widget)
        if not value:
            return None

        new_value = self.convert_from_multiple_formats(value, ('%d/%m/%Y','%d/%m/%y','%d.%m.%Y','%d.%m.%y','%d %m %Y','%d %m %y'))

        if new_value is not None:
            return new_value

        # Human valid values
        today = datetime.date.today()
        if str(value).lower() in ('today','tdy'):
            return today
        elif str(value).lower() in ('tomorrow','tmr'):
            return today + datetime.timedelta(days=1)
        elif str(value).lower() in self.WEEK_DAYS:
            # This code finds the next date for the week day given
            week_day = self.WEEK_DAYS[str(value).lower()]
            return today + datetime.timedelta(days=(week_day+7-today.weekday())%7 or 7)

        raise ValidationError('Invalid date format: %s'%value)


class TimeField(Field):
    widget = TimeInput
    EXP_MIN = re.compile('(\d+)[ ]*(min|minute)s?')
    EXP_HOUR = re.compile('(\d+)[ ]*(hr|hour)s?')

    def __init__(self, **kwargs):
        super(TimeField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' time_field'

    def convert_from_multiple_formats(self, value, formats):
        for fmt in formats:
            try:
                return datetime.datetime.strptime(value, fmt).time()
            except ValueError:
                pass

    def clean(self, value):
        value = super(TimeField, self).clean(value)

        # FIXME: this method shouldn't be here and the datetime formats below as well (they should be in the widget)
        if not value:
            return None

        new_value = self.convert_from_multiple_formats(value, ('%H:%M:%S','%H:%M','%H','%H%M','%H %M','%H.%M','%H,%M'))

        if new_value is not None:
            return new_value

        # Human valid values
        if str(value).lower() == 'now':
            return datetime.datetime.now().time()

        # Humanized formats
        minute = None
        found_min = self.EXP_MIN.findall(value)
        if found_min:
            minute = int(found_min[0][0])
        hour = None
        found_hr = self.EXP_HOUR.findall(value)
        if found_hr:
            hour = int(found_hr[0][0])
        if minute is not None or hour is not None:
            return (datetime.datetime.now() + datetime.timedelta(seconds=(minute or 0)*60 + (hour or 0)*60*60)).time()

        raise ValidationError('Invalid time format: %s'%value)


class DateTimeField(Field):
    widget = DateTimeInput

    def __init__(self, **kwargs):
        super(DateTimeField, self).__init__(**kwargs)
        self.attrs.setdefault('class','')
        self.attrs['class'] += ' datetime_field'

    def clean(self, value):
        value = super(DateTimeField, self).clean(value)

        # FIXME: this method shouldn't be here and the datetime formats below as well (they should be in the widget)
        if not value or isinstance(value, (datetime.datetime, datetime.date)):
            return value

        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    return datetime.datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
                except ValueError:
                    try:
                        return datetime.datetime.strptime(value, '%d/%m/%Y %H:%M')
                    except ValueError:
                        raise ValidationError('Invalid datetime format: %s'%value)


class MarkdownField(Field):
    widget = Textarea
    
    # Try to import markdonw2
    try:
        import markdown2
    except ImportError:
        markdown2 = None
        #raise ValidationError('Cannot import markdown2')
    
    def clean(self, value):
        value = super(MarkdownField, self).clean(value)
        if not isinstance(value, basestring):
            raise ValidationError('Invalid type. Expected string: %s'%value)
        
        try:                
            value = markdown2.markdown(mark_safe(value))
        except:
            raise ValidationError('Error markdown: %s'%value)
            #value = ''
        else:
            return value or ''
