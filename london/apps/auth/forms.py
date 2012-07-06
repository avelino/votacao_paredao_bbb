from london import forms
from london.apps.auth.tokens import default_token_generator
from london.apps.auth.models import User
from london.urls import reverse
from london.http import HttpResponseRedirect
from london.utils.translation import ugettext as _
from london.apps.auth import app_settings
from london.utils.imports import import_anything
from london.utils.validation import REGEX_EMAIL_ADDRESS
from london.db.models import PersistentModel


def get_user_for_reset(request, queryset, cleaned_data):
    if isinstance(queryset, PersistentModel):
        queryset = queryset.query()

    # Validates and loads the user for username or e-mail given
    if REGEX_EMAIL_ADDRESS.match(cleaned_data['email_or_username']):
        try:
            return queryset.get(email=cleaned_data['email_or_username'])
        except queryset.model.DoesNotExist:
            pass

    else:
        try:
            return queryset.get(username=cleaned_data['email_or_username'])
        except queryset.model.DoesNotExist:
            pass


class ResetPasswordForm(forms.Form):
    email_or_username = forms.CharField(max_length=50, required=False)
    
    def __init__(self, request, user_class=User, queryset=None,
            template_name='auth/reset_password_form.html',
            token_generator=default_token_generator,
            url_sent='london.apps.auth.views.reset_password_sent',
            url_confirmation='london.apps.auth.forms.ResetPasswordConfirmForm',
            mail_template='password_reset_send_token',
            get_user_function=get_user_for_reset,
            ):
        self._meta.template = template_name
        self.token_generator = token_generator
        self.url_sent = url_sent
        self.url_confirmation = url_confirmation
        self.user_class = user_class
        self.queryset = queryset
        self.mail_template = mail_template
        self.get_user_function = get_user_function or get_user_for_reset

        super(ResetPasswordForm, self).__init__(request=request)

    def clean(self):
        data = super(ResetPasswordForm, self).clean()

        # Validates and loads the user for username or e-mail given
        queryset = self.queryset or self.user_class.query()
        self.user = self.get_user_function(self.request, queryset, data)

        if not self.user:
            raise forms.ValidationError('User not found.')

        return data

    def http_post(self, *args, **kwargs):
        if self.is_valid():
            # Generates a token
            token = self.token_generator.make_token(self.user)
            self.user['reset_password_token'] = token
            self.user.save()

            # URLs
            url_sent = reverse(self.url_sent, service=self.request.service)
            url_confirmation = reverse(self.url_confirmation, kwargs={'token':token}, service=self.request.service)
            
            # Sends an e-mail message with the token for password reset
            send_token = import_anything(app_settings.PASSWORD_RESET_SEND_TOKEN)
            send_token(site=self.request.site, user=self.user, token=token, url_sent=url_sent,
                    url_confirmation=url_confirmation, mail_template=self.mail_template)

            return HttpResponseRedirect(url_sent)
        return {}


class ResetPasswordConfirmForm(forms.Form):
    email_or_username = forms.EmailField()
    new_password = forms.PasswordField()
    confirm_password = forms.PasswordField()

    def __init__(self, request, token, user_class=User, queryset=None,
            template_name='auth/reset_password_confirm_form.html',
            token_generator=default_token_generator,
            url_invalid='london.apps.auth.views.reset_password_invalid',
            url_finished='london.apps.auth.views.reset_password_finished',
            get_user_function=get_user_for_reset,
            ):
        self._meta.template = template_name
        self.token = token
        self.url_invalid = url_invalid
        self.url_finished = url_finished
        self.user_class = user_class
        self.queryset = queryset
        self.get_user_function = get_user_function or get_user_for_reset

        # Validates the given token
        try:
            queryset = self.queryset or self.user_class.query()
            self.user = queryset.get(reset_password_token=token)
        except self.user_class.DoesNotExist:
            self.user = None

        super(ResetPasswordConfirmForm, self).__init__(request=request)

    def clean(self):
        data = super(ResetPasswordConfirmForm, self).clean()

        # Validates and loads the user for username or e-mail given
        queryset = self.queryset or self.user_class.query()
        email_user = self.get_user_function(self.request, queryset, data)

        if not email_user or email_user != self.user:
            raise forms.ValidationError(_('Invalid e-mail for this token.'))

        if data['new_password'] != data['confirm_password']:
            raise forms.ValidationError(_('Invalid password confirmation.'))

        return data

    def http_get(self, *args, **kwargs):
        if not self.user:
            return HttpResponseRedirect(reverse(self.url_invalid, service=self.request.service))

    def http_post(self, *args, **kwargs):
        if not self.user:
            return HttpResponseRedirect(reverse(self.url_invalid, service=self.request.service))

        if self.is_valid():
            self.user['password'] = self.cleaned_data['new_password']
            self.user['reset_password_token'] = None
            self.user.save()

            return HttpResponseRedirect(reverse(self.url_finished, service=self.request.service))

