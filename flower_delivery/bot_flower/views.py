from aiogram import Bot  
from django.conf import settings  # для получения токена бота  
from .models import TelegramOrder, TelegramUser
from aiogram.types import Message
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

async def webhook(request):
    if request.method == 'POST':
        data = await request.json()

        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user = get_object_or_404(TelegramUser, telegram_id=chat_id)
            order = get_object_or_404(TelegramOrder, user=user)

            if 'text' in message:
                text = message['text']

async def send_order_confirmation(order):
    user = TelegramUser.objects.get(user=order.user)  # предполагаем, что у заказа есть связь с пользователем
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    message = f"Ваш заказ №{order.id} успешно оформлен!\n" \
              f"Детали заказа: {order.items_list()}\n" \
              f"Сумма: {order.total_price}\n" \
              f"Адрес доставки: {order.delivery_address}\n" \
              f"Телефон: {order.phone_number}\n"
    await bot.send_message(chat_id=user.telegram_id, text=message)

