from django.shortcuts import render

def index(request):
    return render(request, 'frontend/index.html')

def stats(request):
    context = {
        'users_count': 1,
        'orders_count': 1,
        'products_count': 5,
    }
    return render(request, 'frontend/stats.html', context)

def auth(request):
    context = {
        'users_count': 1,
        'orders_count': 1,
        'products_count': 5,
    }
    return render(request, 'frontend/auth.html', context)