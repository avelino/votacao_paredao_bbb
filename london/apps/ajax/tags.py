from london.http import HttpResponseRedirect

def redirect_to(request, url, no_history=False):
    if request.is_ajax():
        return '<redirect url="%s"%s/>'%(url, ' rel="nohistory"' if no_history else '')
    else:
        return HttpResponseRedirect(url)

