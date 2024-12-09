from django.conf import settings
from django.db import models
from aiogram import Bot


class TelegramUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField(unique=True)  # Убрали max_length
    user_orders = models.ManyToManyField('flowers.Order', related_name='telegram_user_orders', blank=True)
    TG_username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=10, default='user')

    class Meta:
        verbose_name = 'Пользователь Telegram'
        verbose_name_plural = 'Пользователи Telegram'

    def save(self, *args, **kwargs):
        if self.TG_username and not self.TG_username.startswith('@'):
            self.TG_username = f'@{self.TG_username}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.TG_username if self.TG_username else "Без имени"


class TelegramOrder(models.Model):
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=50)
    bouquet_details = models.TextField()  # Данные о букете
    delivery_method = models.CharField(max_length=20)  # Курьер или самовывоз
    payment_method = models.CharField(max_length=20)  # способ оплаты
    status = models.CharField(max_length=50, default='Новый')  # Статус заказа

    async def change_status(self, new_status):
        self.status = new_status
        await self.save()  # Используйте await, если save() асинхронная
        # После изменения статуса, отправляем уведомление
        await self.notify_user()

    async def notify_user(self):
        user_profile = TelegramUser.objects.get(user=self.user)  # аналогично как выше
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        message = f"Ваш заказ №{self.id} от {self.created_at.strftime('%d-%m-%Y')} " \
                  f"изменён на статус: {self.status}\n"
        await bot.send_message(chat_id=user_profile.telegram_id, text=message)

    def items_list(self):
        return self.bouquet_details

    def __str__(self):
        return f"Заказ №{self.order_id} пользователя {self.telegram_user.user.username} от {self.order.order_date}"