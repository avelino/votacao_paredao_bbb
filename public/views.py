import os
import time
import datetime
import simplejson

from london.templates import render_template
from london.http import HttpResponse
from london.http import HttpResponseRedirect
from london.sse import server_sent_event_source
from london.apps.ajax.tags import redirect_to
from london import forms

from models import Votes, SEAWALL

class HomeForm(forms.ModelForm):
    class Meta:
        template = 'home'
        model = Votes
        fields = ('result')
        ajax_post_json_response = True

    result = forms.ChoiceField(choices=SEAWALL)

    def ajax_post(self, *args, **kwargs):
        return self.http_post(*args, **kwargs)

    def http_post(self, *args, **kwargs):
        if not self.errors:
            return redirect_to(self.request, '/')

