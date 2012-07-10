from london import forms
from london.apps.auth.models import User
from london.apps.auth import app_settings
from london.exceptions import ValidationError
from london.http import HttpResponseRedirect
from london.apps.ajax.tags import redirect_to
from london.apps.auth.authentication import user_login

class AuthForm(forms.Form):
    class Meta:
        template = 'admin/login.html'

    username = forms.CharField(max_length=100)
    password = forms.PasswordField()
    next = forms.Field(widget=forms.HiddenInput, required=False)

    def http_post(self, *args, **kwargs):
        from london.apps import admin
        if self.is_valid():
            user_login(self.request, self.user)
            url = self.cleaned_data.get('next', None) or admin.site.root_url
            return redirect_to(self.request, url)

        return {'admin_site': admin.site}

    def ajax_post(self, *args, **kwargs):
        return self.http_post(*args, **kwargs)

    def clean(self):
        data = super(AuthForm, self).clean()

        try:
            self.user = User.query().get(username=data['username'])
        except User.DoesNotExist:
            raise ValidationError('User with username "%s" not found.'%data['username'])

        if not self.user.is_valid_password(data['password']):
            raise ValidationError('Invalid password!')

        return data

class ChangePasswordForm(forms.Form):
    class Meta:
        template = 'admin/change_password.html'

    old_password = forms.PasswordField()
    new_password = forms.PasswordField()
    confirm_password = forms.PasswordField()
    next = forms.Field(widget=forms.HiddenInput, required=False)

    def clean(self):
        data = super(ChangePasswordForm, self).clean()

        # Check old password
        if not self.request.user.is_valid_password(data['old_password']):
            raise ValidationError('Invalid old password.')

        # Validates password confirmation
        if data['new_password'] != data['confirm_password']:
            raise ValidationError('Invalid password confirmation.')

        return data

    def http_post(self, *args, **kwargs):
        if self.is_valid():
            self.request.user['password'] = self.cleaned_data['new_password']
            self.request.user.save()
            url = self.cleaned_data.get('next', None) or app_settings.LOGIN_REDIRECT_URL
            return redirect_to(self.request, url)

        return {}

    def ajax_post(self, *args, **kwargs):
        return self.http_post(*args, **kwargs)

