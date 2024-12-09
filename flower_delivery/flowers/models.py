from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import datetime

# Модель пользователя
class CustomUser(AbstractUser):

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'password']
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Админ'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    # Добавление related_name для устранения конфликта
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
        verbose_name='Группы',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Разрешения, назначенные этому пользователю.',
        verbose_name='Разрешения',
    )

    def __str__(self):
        return self.username

# Модель профиля пользователя
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    avatar = models.ImageField(upload_to='flowers/static/flowers/img/avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

# Модель товара
class Product(models.Model):
    name = models.CharField(max_length=100)  # Название товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара
    image = models.ImageField(upload_to='static/flowers/img/catalog/')  # Изображение товара

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):  # корректное отображение на странице
        return self.name

# Модель корзины
class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'

# Модель заказа
class Order(models.Model):
    STATUS_CHOICES = [
        ('Новый', 'Новый'),
        ('В процессе', 'В процессе'),
        ('Готов к выдаче', 'Готов к выдаче'),
        ('Завершен', 'Завершен'),
        ('Отменен', 'Отменен'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Связывает заказ с пользователем
    telegram_user = models.ForeignKey('bot_flower.TelegramUser', on_delete=models.CASCADE, null=True, blank=True)  # Связывает заказ с пользователем Telegram
    product = models.ManyToManyField(Product)  # Связывает заказ с продуктами
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Новый')  # Статус заказа
    order_date = models.DateTimeField(auto_now_add=True)  # Дата заказа
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_method = models.CharField(max_length=100, default='Самовывоз')
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price_with_delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=100, default='Наличные')


    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):  # корректное отображение на странице
        return f'Заказ №{self.id} от пользователя {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items',on_delete=models.CASCADE)  # Связывает товар с заказом
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Связывает товар с продуктом
    quantity = models.PositiveIntegerField(default=1)  # Количество
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.product.price
        self.total_price = self.amount  # Здесь можно расширить логику для общей суммы
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product.name} - {self.quantity} шт. на сумму {self.amount} руб. в заказе {self.order.id}'

# Модель отзыва
class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Связывает отзыв с пользователем
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Связывает отзыв с продуктом
    review_text = models.TextField()  # Текст отзыва
    rating = models.IntegerField()  # Рейтинг (1-5)


    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):  # корректное отображение на странице
        return f'Отзыв о {self.product.name} от {self.user.username}'

# Модель отчета
class Report(models.Model):
    orders = models.TextField(default='')  # Хранит все IDs заказов в виде строки
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)  # Общая сумма продаж
    count = models.IntegerField(default=0)  # Количество заказов в отчёте
    start_date = models.DateField(default=datetime.datetime.now)  # Дата начала продаж
    end_date = models.DateField(default=datetime.datetime.now)  # Дата окончания продаж
    report_date = models.DateTimeField(auto_now_add=True)  # Дата создания отчета

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'

    def __str__(self):  # корректное отображение на странице
        return f'Отчет {self.id} о продажах от {self.report_date}'



