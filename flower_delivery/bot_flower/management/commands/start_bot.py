from django.core.management.base import BaseCommand
from .bot_flower import dp
from aiogram import executor

class Command(BaseCommand):
    help = 'Запустить Telegram-бота'

    def handle(self, *args, **kwargs):
        executor.start_polling(dp)