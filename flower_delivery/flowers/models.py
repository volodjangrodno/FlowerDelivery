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

    avatar = models.ImageField(upload_to='media/avatars/', default='media/avatars/default_user.png', blank=True)
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
class EditProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    avatar = models.ImageField(upload_to='media/avatars/', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'Профиль пользователя {self.user.email}'

# Модель товара
class Product(models.Model):
    name = models.CharField(max_length=100)  # Название товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара
    image = models.ImageField(upload_to='flowers/static/flowers/img/')  # Изображение товара

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
        ('New', 'Новый'),
        ('Processing', 'В обработке'),
        ('Completed', 'Завершен'),
        ('Cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Связывает заказ с пользователем
    products = models.ManyToManyField(Product)  # Связывает заказ с продуктами
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Новый')  # Статус заказа
    order_date = models.DateTimeField(auto_now_add=True)  # Дата заказа


    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):  # корректное отображение на странице
        return f'Заказ #{self.id} от {self.user.username}'

# Модель товаров в заказе
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Связывает товар с заказом
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Связывает товар с продуктом
    quantity = models.PositiveIntegerField(default=1)  # Количество
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):  # корректное отображение на странице
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
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Связывает отчет с заказом
    sale_data = models.DecimalField(max_digits=10, decimal_places=2)  # Данные по продажам
    profit = models.DecimalField(max_digits=10, decimal_places=2)  # Прибыль
    expenses = models.DecimalField(max_digits=10, decimal_places=2)  # Расходы
    report_date = models.DateTimeField(auto_now_add=True)  # Дата создания отчета

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'

    def __str__(self):  # корректное отображение на странице
        return f'Отчет для заказа #{self.order.id} от {self.report_date}'

class SaleReport(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Отчет о продаже'
        verbose_name_plural = 'Отчеты о продажах'

    def __str__(self):  # корректное отображение на странице
        return f"Отчет о продаже {self.order.id} на сумму {self.total_amount} руб."

