from london.forms.base import Form, FormRenderer
from london.forms.fields import Field
from london.forms.widgets import Widget
from london.utils.datastructures import SortedDict

class FormsetRenderer(Widget):
    formset = None
    attrs = None

    def __init__(self, formset=None, attrs=None):
        self.formset = formset or self.formset
        self.attrs = attrs or self.attrs or {}
        super(FormsetRenderer, self).__init__()

    def render(self, name, value, attrs=None):
        forms = []
        for num, item in enumerate(value):
            form_class = self.formset.get_form()
            forms.append(self.render_item('%s-%s-'%(name, num), item, form_class, attrs))
        return u'\n'.join([form.render() for form in forms])

    def render_item(self, prefix, item, form_class, attrs):
        form = form_class()
        form.instance = item
        return FormRenderer(form, form.get_initial(), prefix=prefix)

    def render_label(self, name, label):
        return u'<h3 id="%s">%s</h3>'%(self.attrs.get('id', name), label)

class FormsetMeta(object):
    def __init__(self, form):
        meta = getattr(form, 'Meta', None)
        if meta:
            for attr in dir(meta):
                if not attr.startswith('_'):
                    setattr(self, attr, getattr(meta, attr))

class BaseFormset(Field):
    renderer = FormsetRenderer
    form = Form
    
    def get_widget(self, form):
        if isinstance(self.renderer, Widget):
            return self.renderer
        
        self.renderer = self.renderer(formset=self)
        return self.renderer

    def get_form(self):
        return self.form

class NestedFormsetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if bases[0] != BaseFormset:
            fields = []
            for attr, obj in attrs.items():
                if not isinstance(obj, Field): continue
                obj.name = attr
                fields.append((attr, attrs.pop(attr)))
            fields.sort(key=lambda x: x[1].creation_counter)
            fields = SortedDict(fields)

        new_class = super(NestedFormsetMetaclass, cls).__new__(cls, name, bases, attrs)

        if bases[0] != BaseFormset:
            new_class._meta = FormsetMeta(new_class)
            new_class._meta.fields = fields

        return new_class

class BaseNestedFormset(BaseFormset):
    pass

