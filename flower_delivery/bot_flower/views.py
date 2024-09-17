from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'bot_flower/bot_home.html')