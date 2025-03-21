from django.http import HttpResponseRedirect, HttpResponse

from gdwrapper.settings import HOME_PAGE_URL
from .GoogleApiClient import GoogleApiClient


def auth(request):
    auth_url = GoogleApiClient.authorizeUser()
    if auth_url:
        return HttpResponseRedirect(auth_url)
    else:
        return HttpResponse('Уже авторизован')


def callback(request):
    code = request.GET.get('code')
    if code:
        GoogleApiClient.createUserToken(code)
        return HttpResponseRedirect(HOME_PAGE_URL)
    else:
        return HttpResponse("Не получен параметр code.")
