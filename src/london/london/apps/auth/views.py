from london.templates import render_to_response
from london.apps.mailing.shortcuts import send_message
from london.apps.mailing.models import MessageTemplate
from london.apps.auth import app_settings

def reset_password_sent(request, template_name='auth/reset_password_sent.html', next_url='/'):
    return render_to_response(request, template_name, {'next_url':next_url})

def reset_password_invalid(request, template_name='auth/reset_password_invalid.html', next_url='/'):
    return render_to_response(request, template_name, {'next_url':next_url})

def reset_password_finished(request, template_name='auth/reset_password_finished.html', next_url='/'):
    return render_to_response(request, template_name, {'next_url':next_url})

def send_token(site, user, token, url_sent, url_confirmation, mail_template):
    tpl, new = MessageTemplate.query().get_or_create(
        name=mail_template,
        defaults={
            'subject': 'Password reset token',
            'body': 'Hello {{ user.name }}, please go to {{ url_confirmation }} to set a new password.',
            },
        )

    return send_message(
            site=site,
            to=user['email'],
            template=tpl,
            context={
                'user':user,
                'token':token,
                'url_sent':site.format_url(url_sent),
                'url_confirmation':site.format_url(url_confirmation),
                },
            )

