from django.db import models
from django.contrib.auth.models import User

# Модель товара
class Product(models.Model):
    name = models.CharField(max_length=100)  # Название товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара
    image = models.ImageField(upload_to='products/')  # Изображение товара

    def __str__(self):
        return self.name

# Модель заказа
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Ожидание'),
        ('Processing', 'В обработке'),
        ('Completed', 'Завершен'),
        ('Cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Связывает заказ с пользователем
    products = models.ManyToManyField(Product)  # Связывает заказ с продуктами
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')  # Статус заказа
    order_date = models.DateTimeField(auto_now_add=True)  # Дата заказа

    def __str__(self):
        return f'Заказ #{self.id} от {self.user.username}'

# Модель отзыва
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Связывает отзыв с пользователем
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Связывает отзыв с продуктом
    review_text = models.TextField()  # Текст отзыва
    rating = models.IntegerField()  # Рейтинг (1-5)

    def __str__(self):
        return f'Отзыв о {self.product.name} от {self.user.username}'

# Модель отчета
class Report(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Связывает отчет с заказом
    sale_data = models.DecimalField(max_digits=10, decimal_places=2)  # Данные по продажам
    profit = models.DecimalField(max_digits=10, decimal_places=2)  # Прибыль
    expenses = models.DecimalField(max_digits=10, decimal_places=2)  # Расходы
    report_date = models.DateTimeField(auto_now_add=True)  # Дата создания отчета

    def __str__(self):
        return f'Отчет для заказа #{self.order.id} от {self.report_date}'

class SaleReport(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Отчет о продаже {self.order.id} на сумму {self.total_amount} руб."

