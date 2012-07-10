import datetime
import decimal
from london.db import models
from london.utils.datatypes import Money

class DBLogQuerySet(models.QuerySet):
    def logs_for_object(self, obj, reverted_order=False):
        return self.filter(object=obj).order_by(('-' if reverted_order else '')+'revision')

    def latest_revision_for_object(self, obj):
        try:
            return self.logs_for_object(obj, reverted_order=True)[0]['revision']
        except IndexError:
            return 0

    def log_save(self, obj, new=False):
        # Gets names of changed field
        fields = self._get_fields(obj)
        if not fields:
            return

        # Gets the previous revision to increment and get the next one
        previous_revision = self.latest_revision_for_object(obj)
        values = dict([(name,self._prepare_field_value(obj, name)) for name in fields])

        return self.model(
            _save=True,
            object=obj,
            action=self.model.ACTION_CREATED if new else self.model.ACTION_CHANGED,
            fields=values,
            revision=previous_revision+1,
            user=self._get_user_for_log(obj),
            )

    def log_delete(self, obj):
        previous_revision = self.latest_revision_for_object(obj)

        return self.model(
            _save=True,
            object=obj,
            action=self.model.ACTION_DELETED,
            revision=previous_revision+1,
            user=self._get_user_for_log(obj),
            )

    def _get_fields(self, obj):
        log_class = obj.Log
        fields = getattr(log_class, 'fields', obj._meta.fields.keys())

        # Removes fields from exclude list
        fields = [name for name in fields if name not in getattr(log_class, 'exclude', [])]
        
        # Removes unchanged fields
        if not getattr(log_class, 'store_unchanged_fields', False):
            fields = [name for name in fields if obj[name] != obj._old_values[name]]

        return fields

    def _prepare_field_value(self, obj, field_name):
        value = obj[field_name]
        if isinstance(value, models.querysets.BaseQuerySet):
            value = [dict([(name,self._prepare_field_value(item, name)) for name in item._meta.fields.keys()])
                    for item in value]
        elif isinstance(value, models.Model):
            value = {'class':value._meta.path_label, 'pk':value['pk']}
        elif isinstance(value, (decimal.Decimal,Money)):
            value = float(value)
        return value

    def _get_user_for_log(self, obj):
        # Method to get user who made the action
        user = None
        get_user_function = getattr(obj, getattr(obj.Log, 'get_user_function', 'get_user_for_log'), None)
        if get_user_function:
            user = get_user_function()
        return user

class DBLog(models.Model):
    class Meta:
        ordering = ('revision',)
        query = 'london.apps.dblogs.models.DBLogQuerySet'

    ACTION_CREATED = 'created'
    ACTION_CHANGED = 'changed'
    ACTION_DELETED = 'deleted'
    ACTION_CHOICES = (
        (ACTION_CREATED, 'Created'),
        (ACTION_CHANGED, 'Changed'),
        (ACTION_DELETED, 'Deleted'),
        )

    object = models.ForeignKey()
    log_time = models.DateTimeField(default=datetime.datetime.now, blank=True, db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    fields = models.DictField(null=True, blank=True)
    revision = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(null=True, blank=True)

    def get_fields_dict(self):
        def get_field_display(field_name):
            try:
                return self['object']._meta.fields[field_name].get_verbose_name()
            except (KeyError, AttributeError):
                return field_name
        return dict([(get_field_display(k), v) for k,v in self['fields'].items()])

# SIGNALS
from london.db.signals import pre_save, pre_delete, post_save, post_delete

def general_pre_save(instance, **kwargs):
    instance._db_old_values = instance._old_values.copy()
pre_save.connect(general_pre_save)

def general_post_save(instance, **kwargs):
    if not hasattr(instance, 'Log') or getattr(instance.Log, 'manual_for_save', False):
        return
    DBLog.query().log_save(instance, new=kwargs.get('new', False))
post_save.connect(general_post_save)

def general_post_delete(instance, **kwargs):
    if not hasattr(instance, 'Log') or getattr(instance.Log, 'manual_for_delete', False):
        return
    DBLog.query().log_delete(instance)
post_delete.connect(general_post_delete)

