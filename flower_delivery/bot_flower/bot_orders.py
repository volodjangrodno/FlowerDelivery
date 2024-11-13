import asyncio
import logging
import sys
from pathlib import Path
from os import getenv
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv

from .models import TelegramUser
from flower_delivery.flowers.models import Order


# Загрузка переменных окружения
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Получение токена бота из переменных окружения
TELEGRAM_BOT_TOKEN = getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    sys.exit("Ошибка: необходимо установить TELEGRAM_BOT_TOKEN в файле .env")

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)  # Устанавливаем уровень логирования

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()




@dp.message(Command("orders"))
async def my_orders(message: Message):
    chat_id = message.chat.id
    user = TelegramUser.objects.get(chat_id=chat_id)
    orders = Order.objects.filter(telegram_user=user)

    if not orders:
        await message.answer("У вас нет текущих заказов.")
        return

        # Формируем inline-кнопки для каждого заказа
    keyboard = InlineKeyboardMarkup()

    for order in orders:
        button = InlineKeyboardButton(
            text=f"Заказ №{order.id} от {order.order_date} на сумму {order.total_price}",
            callback_data=f"order_details:{order.id}"  # Передаем ID заказа
        )
        keyboard.add(button)

    await message.answer("Ваши заказы:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('order_details:'))
async def process_order_detail(callback_query: CallbackQuery):
    order_id = callback_query.data.split(':')[1]  # Извлекаем ID заказа
    order = Order.objects.get(id=order_id)  # Получаем заказ из базы

    # Формируем сообщение с деталями заказа
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

    await callback_query.answer()  # Убираем индикатор загрузки
    await callback_query.message.answer(details_message)  # Отправляем сообщение с деталями






