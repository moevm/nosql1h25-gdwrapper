from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from .GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService
from gdwrapper.handlers import refresh_data_in_mongo


def auth(request):
    auth_url = GoogleApiClient.authorizeUser()
    if auth_url:
        return HttpResponseRedirect(auth_url)
    else:
        return HttpResponse('Уже авторизован')


def logout(request):
    GoogleApiClient.logout()
    mongo_service = MongoService()
    mongo_service.refresh_documents({})
    return HttpResponseRedirect(reverse('index'))


def callback(request):
    code = request.GET.get('code')
    if code:
        GoogleApiClient.createUserToken(code)
        refresh_data_in_mongo()
        return HttpResponseRedirect(reverse('index'))
    else:
        return HttpResponse("Не получен параметр code.")
