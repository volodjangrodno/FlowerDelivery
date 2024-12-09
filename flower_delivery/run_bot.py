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
from flowers.models import CustomUser, Profile, Order, Report
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

@dp.message(Command('orders'))
async def all_orders(message: Message):
    chat_id = message.from_user.id
    telegram_user = await TelegramUser.objects.aget(chat_id=chat_id)

    # Проверяем роль пользователя
    if telegram_user.role != 'admin':
        await message.answer("У вас нет прав для доступа к списку всех заказов.")
        return

    # Получаем все отчеты
    orders = await sync_to_async(list)(Order.objects.all())

    if not orders:
        await message.answer("Нет списка доступных заказов.")
        await message.edit_text("Нет списка доступных заказов.", reply_markup=kb.start_keyboard)
        return

        # Формируем сообщение со всеми заказами
    orders_message = 'Список всех заказов:\n'

    # Создаем клавиатуру для отчетов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for order in orders:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Заказ №{order.id} от {order.order_date.strftime('%d-%m-%Y %H:%M')} на сумму {order.total_price_with_delivery} руб.",
                callback_data=f'order_details:{order.id}'
            )
        ])

    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_start")
    ])

    await message.answer(orders_message, reply_markup=keyboard)



async def send_order_confirmation(chat_id, order):
    # Получаем пользователя Telegram асинхронно
    user = await sync_to_async(TelegramUser.objects.get)(user=order.user)  # предполагаем, что у заказа есть связь с пользователем
    # Получаем продукты из заказа
    products = await sync_to_async(list)(order.orderitem_set.all())  # Получаем все продукты из заказа

    # Формируем сообщение
    product_list = "\n".join([f"{item.product.name} (количество: {item.quantity})" for item in products])
    message = (
        f"Ваш заказ №{order.id} успешно оформлен!\n"  
        f"Продукты в заказе:\n{product_list}\n"  
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
    await bot.send_message(chat_id=chat_id, text=message)


async def send_order_status_update(order):
    user = await sync_to_async(TelegramUser.objects.get)(user=order.user)

    message = (
        f"Статус вашего заказа №{order.id} изменён на \"{order.status}\"!\n"  
        f"Продукты в заказе: {order.products}\n"  
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


@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    chat_id = callback.from_user.id

    # Получаем пользователя Telegram
    telegram_user = await TelegramUser.objects.select_related('user').aget(chat_id=chat_id)

    # Получаем все заказы, связанные с этим пользователем
    orders = await sync_to_async(list)(Order.objects.filter(telegram_user=telegram_user))

    if not orders:
        await callback.answer("У вас нет текущих заказов.")
        await callback.message.answer("У вас нет текущих заказов.", reply_markup=kb.start_keyboard)
        return

    # Формируем сообщение с заказами
    orders_message = 'Мои заказы:\n'

    # Создаем клавиатуру в формате списка списков
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for order in orders:
        # Создаем кнопку для каждого заказа
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Заказ №{order.id} от {order.order_date.strftime('%d-%m-%Y %H:%M')} на сумму {order.total_price_with_delivery} руб.",
                callback_data=f'order_details:{order.id}'
            )
        ])

    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_start")
    ])

    await callback.message.answer(orders_message, reply_markup=keyboard)



@dp.callback_query(lambda c: c.data.startswith('order_details:'))
async def process_order_detail(callback_query: CallbackQuery):
    order_id = callback_query.data.split(':')[1]

    # Получаем заказ, используя sync_to_async
    order = await sync_to_async(Order.objects.get)(id=order_id)

    # Получаем пользователя асинхронно
    user = await sync_to_async(lambda: order.user)()  # Используем лямбда-функцию для получения пользователя

    # Получаем продукты заказа асинхронно
    products = await sync_to_async(list)(order.product.all())

    details_message = (
        f"Детали заказа №{order.id}\n"  
        f"Дата заказа: {order.order_date.strftime('%d-%m-%Y %H:%M')}\n" 
        f"Заказчик: {user}\n"
        f"Продукты: {', '.join([product.name for product in products])}\n"  
        f"Статус: {order.status}\n"  
        f"Сумма: {order.total_price} руб.\n"  
        f"Способ доставки: {order.delivery_method}\n"  
        f"Адрес доставки: {order.address}\n"  
        f"Телефон: {order.phone_number}\n"  
        f"Стоимость доставки: {order.delivery_price} руб.\n"  
        f"Итого с доставки: {order.total_price_with_delivery} руб.\n"  
        f"Способ оплаты: {order.payment_method}\n"
    )

    # Создаем кнопку "Назад"
    back_keyboards = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="back_to_orders"),
            InlineKeyboardButton(text="Проверить статус", callback_data=f"check_status_{order.id}")
        ]
    ])

    await callback_query.answer()
    await callback_query.message.answer(details_message, reply_markup=back_keyboards)

@dp.callback_query(lambda c: c.data == "back_to_orders")
async def back_to_orders(callback: CallbackQuery):
    # Возвращаемся к списку заказов
    await my_orders(callback)

@dp.callback_query(lambda c: c.data.startswith("check_status_"))
async def check_order_status(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    order = await sync_to_async(Order.objects.get)(id=order_id)
    await callback.message.answer(f"Статус вашего заказа: {order.status}")

@dp.callback_query(lambda c: c.data == "analytics")
async def analytics(callback: CallbackQuery):
    chat_id = callback.from_user.id
    telegram_user = await TelegramUser.objects.aget(chat_id=chat_id)

    # Проверяем роль пользователя
    if telegram_user.role != 'admin':
        await callback.answer("У вас нет прав для доступа к аналитике.")
        await callback.message.answer("У вас нет прав для доступа к аналитике.", reply_markup=kb.start_keyboard)
        return

    # Получаем все отчеты
    reports = await sync_to_async(list)(Report.objects.all())

    if not reports:
        await callback.answer("Нет доступных отчетов.")
        await callback.message.answer("Нет доступных отчетов.", reply_markup=kb.start_keyboard)
        return

    # Формируем сообщение с отчетами
    reports_message = 'Список отчетов:\n'

    # Создаем клавиатуру для отчетов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for report in reports:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Отчет №{report.id} от {report.report_date.strftime('%d-%m-%Y %H:%M')} - {report.total_sales} руб.",
                callback_data=f'report_details:{report.id}'
            )
        ])

    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад", callback_data="back_to_start")
    ])

    await callback.message.answer(reports_message, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('report_details:'))
async def process_report_detail(callback_query: CallbackQuery):
    report_id = callback_query.data.split(':')[1]

    # Получаем отчет
    report = await sync_to_async(Report.objects.get)(id=report_id)

    details_message = (
        f"Детали отчета №{report.id}\n"  
        f"Общая сумма продаж: {report.total_sales} руб.\n"  
        f"Количество заказов: {report.count}\n"  
        f"Дата начала: {report.start_date.strftime('%d-%m-%Y')}\n"  
        f"Дата окончания: {report.end_date.strftime('%d-%m-%Y')}\n"  
        f"Дата создания: {report.report_date.strftime('%d-%m-%Y %H:%M')}\n"  
        f"Заказы: {report.orders}\n"  # Здесь можно отформатировать вывод, если нужно
    )

    # Создаем кнопку "Назад"
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="back_to_analytics")
        ]
    ])

    await callback_query.answer()
    await callback_query.message.answer(details_message, reply_markup=back_keyboard)

@dp.callback_query(lambda c: c.data == "back_to_analytics")
async def back_to_analytics(callback: CallbackQuery):
    await analytics(callback)  # Возвращаемся к списку отчетов


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(
        f"С возвращением, {callback.from_user.full_name}! \n"  
        f"Выберите дальнейшее действие в меню ниже.",
        reply_markup=kb.start_keyboard
    )
    await callback.answer()




# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())