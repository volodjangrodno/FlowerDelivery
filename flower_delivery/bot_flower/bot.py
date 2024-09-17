import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from django.conf import settings
from flower_delivery.flowers.models import Order  # Импортируйте вашу модель Order

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для получения заказов
def get_orders():
    return Order.objects.all()  # Получаем все заказы

# Функция для отправки уведомлений о статусе
def send_order_status(update: Update, context: CallbackContext):
    orders = get_orders()
    if not orders:
        update.message.reply_text("Нет заказов.")
        return

    message = "Статусы заказов:\n"
    for order in orders:
        message += f"Заказ #{order.id}: {order.status}\n"  # Предполагается, что у вас есть поле status в модели Order

    update.message.reply_text(message)

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Добро пожаловать! Используйте команду /status для получения статуса заказов.")

# Функция для обновления статуса заказа
def update_order_status(update: Update, context: CallbackContext):
    if len(context.args) != 2:
        update.message.reply_text("Используйте: /update_status <order_id> <new_status>")
        return

    order_id = context.args[0]
    new_status = context.args[1]

    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        update.message.reply_text(f"Статус заказа #{order_id} обновлен на '{new_status}'.")
    except Order.DoesNotExist:
        update.message.reply_text(f"Заказ с ID {order_id} не найден.")

# Функция для получения информации о заказе
def get_order_info(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Используйте: /order_info <order_id>")
        return

    order_id = context.args[0]

    try:
        order = Order.objects.get(id=order_id)
        message = (f"Информация о заказе #{order.id}:\n"  
                   f"Статус: {order.status}\n"  
                   f"Дата создания: {order.created_at}\n"  
                   f"Сумма: {order.total_amount} руб.")  # Предполагается, что у вас есть поле total_amount
        update.message.reply_text(message)
    except Order.DoesNotExist:
        update.message.reply_text(f"Заказ с ID {order_id} не найден.")

# Основная функция для запуска бота
def main():
    # Получите токен из переменных окружения или настройте его напрямую
    token = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')

    updater = Updater(token)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрация обработчиков команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", send_order_status))
    dp.add_handler(CommandHandler("update_status", update_order_status))
    dp.add_handler(CommandHandler("order_info", get_order_info))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


