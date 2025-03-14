from django.shortcuts import render

def index(request):
    return render(request, 'frontend/index.html')

def statistics(request):
    context = {
        'users_count': 1,
        'orders_count': 1,
        'products_count': 5,
    }
    return render(request, 'frontend/statistics.html', context)