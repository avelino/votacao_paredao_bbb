import os
import time
import datetime
import simplejson

from london.templates import render_template
from london.http import HttpResponse
from london.http import HttpResponseRedirect
from london.http import JsonResponse
from london.urls import reverse
from london.apps.ajax.tags import redirect_to
from london.sse import server_sent_event_source
from london.apps.ajax.tags import redirect_to
from london import forms

from models import Votes
from models import SEAWALL


def report():
    p_1 = Votes.query().filter(result='1').count()
    p_2 = Votes.query().filter(result='2').count()

    p1 = 0
    if p_1 != 0:
        p1 = int((p_1*100.00)/(p_1+p_2))
    p2 = 0
    if p_2 != 0:
        p2 = int((p_2*100.00)/(p_1+p_2))

    if p1 == 0 and p2 == 0:
        p1 = 50
        p2 = 50

    return {'p1': p1, 'p2': p2}


class HomeForm(forms.ModelForm):
    class Meta:
        #template = 'result'
        template = 'home'
        model = Votes
        fields = ('result')

    result = forms.CharField(widget=forms.HiddenInput())

    def ajax_post(self):
        return self.http_post(*args, **kwargs)

    def http_post(self):
        if self.is_valid():
            return HttpResponseRedirect(reverse('result'))


@render_template('result')
def Result(request):
    ret = report()
    return locals()
