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
import bot_flower.keyboards as kb

from django.contrib.auth.models import User
from flowers.models import CustomUser, Profile, Order
from bot_flower.models import TelegramUser
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

DATABASE = 'db.sqlite3'  # Путь к базе данных

@dp.message(CommandStart())
async def start(message: Message):
    chat_id = message.from_user.id

    username = message.from_user.username or "пользователь"

    User = get_user_model()

    # Получаем или создаем пользователя
    user_instance, user_created = await sync_to_async(User.objects.get_or_create)(
        username=username
    )

    profile = await sync_to_async(Profile.objects.get)(user=user_instance)

    # Теперь создаем или получаем TelegramUser
    telegram_user, tg_user_created = await sync_to_async(TelegramUser.objects.get_or_create)(
        chat_id=chat_id,
        defaults={
            'chat_id': chat_id,
            'TG_username': f'@{username}',
            'first_name': profile.first_name,  # Добавляем поле first_name
            'last_name': profile.last_name,  # Добавляем поле last_name
            'address': profile.address,  # Добавляем поле address
            'phone_number': profile.phone_number,  # Добавляем phone_number
            'user': user_instance,  # Привязываем к существующему пользователю
            'role': user_instance.role  # Роль пользователя в приложении flowers
        }
    )

    # Сообщение пользователю
    await message.answer(
        f"Привет, {message.from_user.full_name}! "  
        f"\n Я твой помощник по приложению о доставке цветов!"  
        f"\n В зависимости от своей роли в приложении выберите одну из следующих команд:",
        reply_markup=kb.start_keyboard
    )

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    conn = None  # Инициализируем conn заранее
    try:
        chat_id = callback.from_user.id

        # Асинхронное получение TelegramUser по chat_id
        telegram_user = await sync_to_async(TelegramUser.objects.get)(chat_id=chat_id)

        # Получаем user_id из TelegramUser
        user_id = telegram_user.user.id

        # Подключаемся к базе данных асинхронно
        conn = await sync_to_async(sqlite3.connect)(DATABASE)
        cursor = conn.cursor()

        # Асинхронное выполнение запроса
        orders = await sync_to_async(cursor.execute)(
            "SELECT id, order_date, total_price FROM flowers_order WHERE user_id = ?",
            (user_id,)
        )
        # Асинхронное получение всех заказов
        orders = await sync_to_async(orders.fetchall)()

        if not orders:  # Проверяем, есть ли заказы
            await callback.answer("У вас нет текущих заказов.")
            return

            # Формируем сообщение с заказами
        orders_message = 'Мои заказы:\n'
        for order in orders:
            orders_message += f'Заказ №{order.id} от {order.order_date} на сумму {order.total_price} руб.\n'

        await callback.message.edit_text(orders_message)
        await callback.answer()  # Убираем вращающийся индикатор загрузки

    except TelegramUser.DoesNotExist:
        await callback.answer("Пользователь не найден. Пожалуйста, попробуйте еще раз.")
        logging.error("Пользователь не найден в таблице TelegramUser.")
    except Exception as e:
        await callback.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        logging.error(f"Ошибка при получении заказов: {e}")
    finally:
        if conn:
            await sync_to_async(conn.close)()  # Закрываем соединение асинхронно



@dp.callback_query(lambda c: c.data.startswith('order_details:'))
async def process_order_detail(callback_query: CallbackQuery):
    order_id = callback_query.data.split(':')[1]
    order = await sync_to_async(Order.objects.get)(id=order_id)

    details_message = (
        f"Детали заказа №{order.id}\n"  
        f"Дата заказа: {order.order_date}\n"  
        f"Продукты: {order.products}\n"  
        f"Статус: {order.status}\n"   
        f"Сумма: {order.total_price} руб.\n"  
        f"Способ доставки: {order.delivery_method}\n"  
        f"Адрес доставки: {order.delivery_address}\n"  
        f"Телефон: {order.phone_number}\n"  
        f"Стоимость доставки: {order.delivery_price} руб.\n"  
        f"Итого с доставки: {order.total_price_with_delivery} руб.\n"  
        f"Cпособ оплаты: {order.payment_method}\n"
    )

    await callback_query.answer()
    await callback_query.message.answer(details_message)

@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Привет, {callback.from_user.full_name}! "  
        f"\n Я твой помощник по приложению о доставке цветов!"  
        f"\n В зависимости от своей роли в приложении выберите одну из следующих команд:",
        reply_markup=kb.start_keyboard
    )
    await callback.answer()




# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())