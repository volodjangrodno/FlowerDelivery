import unittest
from django.test import TestCase
from telegram import Update
from telegram.ext import CallbackContext
from flower_delivery.flowers.models import Order
from flower_delivery.bot_flower.bot_orders import update_order_status, get_order_info, send_order_status

class BotTests(TestCase):
    def setUp(self):
        # Создание тестового заказа
        self.order = Order.objects.create(status="Новый", total_amount=100.0)

    def tearDown(self):
        # Удаление тестового заказа после тестов
        self.order.delete()

    def test_update_order_status(self):
        update = Update(update_id=1, message=None)  # Создаем объект Update
        context = CallbackContext.from_update(update)

        # Тест успешного обновления статуса
        update_order_status(update, context, args=[self.order.id, "Обработан"])
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "Обработан")

        # Тест несуществующего заказа
        update_order_status(update, context, args=[999, "Обработан"])
        self.assertIn("Заказ с ID 999 не найден.", context.bot.send_message.call_args[0][1])

    def test_get_order_info(self):
        update = Update(update_id=1, message=None)  # Создаем объект Update
        context = CallbackContext.from_update(update)

        # Тест успешного получения информации о заказе
        get_order_info(update, context, args=[self.order.id])
        self.assertIn(f"Информация о заказе #{self.order.id}:", context.bot.send_message.call_args[0][1])

        # Тест несуществующего заказа
        get_order_info(update, context, args=[999])
        self.assertIn("Заказ с ID 999 не найден.", context.bot.send_message.call_args[0][1])

    def test_send_order_status(self):
        update = Update(update_id=1, message=None)  # Создаем объект Update
        context = CallbackContext.from_update(update)

        # Тест отправки статусов заказов
        send_order_status(update, context)
        self.assertIn(f"Заказ #{self.order.id}: {self.order.status}", context.bot.send_message.call_args[0][1])

if __name__ == '__main__':
    unittest.main()
