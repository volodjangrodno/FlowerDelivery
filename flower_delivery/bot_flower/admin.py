from django.contrib import admin

from .models import TelegramOrder, TelegramUser

# Register your models here.

admin.site.register(TelegramUser)
admin.site.register(TelegramOrder)
