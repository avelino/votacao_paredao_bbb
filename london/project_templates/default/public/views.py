from london.templates import render_template
from london.http import HttpResponse

@render_template('home')
def home(request):
    return {}

