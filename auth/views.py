from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .GoogleApiClient import GoogleApiClient


def auth(request):
    auth_url = GoogleApiClient.authorizeUser()
    if auth_url: return HttpResponseRedirect(auth_url)
    else: return HttpResponse('err')

