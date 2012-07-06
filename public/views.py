import os
import time
import datetime
import simplejson

from london.templates import render_template
from london.http import HttpResponse
from london.http import HttpResponseRedirect
from london.http import JsonResponse
from london.sse import server_sent_event_source
from london.apps.ajax.tags import redirect_to
from london import forms

from models import Votes
from models import SEAWALL


def report():
    p_1 = Votes.query().filter(result='1').count()
    p_2 = Votes.query().filter(result='2').count()
    return {'p1': int((p_1*100.00)/(p_1+p_2)), 'p2': int((p_2*100.00)/(p_1+p_2))}


class Result(forms.ModelForm):
    class Meta:
        template = 'result'
        model = Votes
        fields = ('result')
        ajax_post_json_response = True

    result = forms.CharField(widget=forms.HiddenInput())

    def ajax_post(self, *args, **kwargs):
        return self.http_post(*args, **kwargs)

    def http_post(self):
        ret = report()
        ret['post'] = 1
        return ret

    def http_get(self):
        return report()


@render_template('home')
def HomeForm(request):
    form = Result
    return locals()
