import os
import sys
import asyncio
import logging
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from aiogram import Router

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')  # Укажите правильный путь к настройкам вашего Django проекта
import django
django.setup()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


from django.contrib.auth.models import User

from .models import TelegramUser
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model  # для получения модели пользователя

# Загрузка переменных окружения
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Получение токена бота из переменных окружения
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    sys.exit("Ошибка: необходимо установить TELEGRAM_BOT_TOKEN в файле .env")

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()



async def send_order_confirmation(order):
    # Получаем пользователя Telegram асинхронно
    user = await sync_to_async(TelegramUser.objects.get)(user=order.user)  # предполагаем, что у заказа есть связь с пользователем


    message = (
        f"Ваш заказ №{order.id} успешно оформлен!\n"  
        f"Детали заказа: {order.products}\n"  
        f"Статус: {order.status}\n"  
        f"Дата заказа: {order.order_date.strftime('%d-%m-%Y %H:%M')}\n"  
        f"Способ доставки: {order.delivery_method}\n"  
        f"Сумма заказа: {order.total_price} руб.\n"  
        f"Стоимость доставки: {order.delivery_price} руб.\n"  
        f"Итого с доставкой: {order.total_price_with_delivery} руб.\n"  
        f"Адрес доставки: {order.address}\n"  
        f"Телефон: {order.phone_number}\n"  
        f"Способ оплаты: {order.payment_method}\n"
    )

    # Асинхронно отправляем сообщение
    await bot.send_message(chat_id=user.telegram_id, text=message)

async def send_order_status_update(order):
    user = await sync_to_async(TelegramUser.objects.get)(user=order.user)

    message = (
        f"Статус вашего заказа №{order.id} изменён на \"{order.status}\"!\n"  
        f"Детали заказа: {order.products}\n"  
        f"Дата заказа: {order.order_date.strftime('%d-%m-%Y %H:%M')}\n"
        f"Сумма заказа: {order.total_price} руб.\n"
        f"Способ доставки: {order.delivery_method}\n"  
        f"Стоимость доставки: {order.delivery_price} руб.\n"
        f"Итого с доставкой: {order.total_price_with_delivery} руб.\n"
        f"Адрес доставки: {order.address}\n"  
        f"Телефон: {order.phone_number}\n"  
        f"Способ оплаты: {order.payment_method}\n"
    )

    # Асинхронно отправляем сообщение
    await bot.send_message(chat_id=user.telegram_id, text=message)