from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import os
import matplotlib.pyplot as plt
import numpy as np
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings # Импортируем settings
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Sum, F
from .forms import CustomUserCreationForm, EditProfileForm
from .models import Product, Order, Review, Report, CustomUser, OrderItem, Profile
from django.utils import timezone
from django.utils.timezone import make_aware
from django.db.models.functions import ExtractDay  # Импортируем ExtractDay
import calendar
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import pytz
from django.urls import reverse
from django import template
from .filters import *


def home(request):
    return render(request, 'flowers/home.html')


# Регистрация пользователя
def register(request):
    error = ''
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создаем профиль и сохраняем данные
            Profile.objects.create(
                user=user,
                username=user.username,
                email=user.email,

            )

            login(request, user)  # Автоматически авторизуем пользователя после регистрации
            return redirect('home')
        else:
            error = form.errors  # Сохраняем ошибки формы
    else:
        error = 'Данные были введены некорректно'
    form = CustomUserCreationForm()
    return render(request, 'flowers/register.html', {'form': form, 'error': error})

# Авторизация пользователя
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if form.is_valid() and user is not None:
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'flowers/login.html', {'form': form})

# Выход пользователя
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')  # 'login' - это имя URL для страницы входа


# Профиль пользователя
@login_required
def profile(request):
    user_profile = Profile.objects.get(user=request.user)  # Получаем профиль
    return render(request, 'flowers/profile.html', {'user': request.user, 'profile': user_profile})

# Редактирование профиля пользователя
@login_required
def edit_profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user_profile)  # Передаем instance
        if form.is_valid():
            # Обновляем аватар, если он был загружен
            if 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']
                file_extension = os.path.splitext(avatar_file.name)[1]
                avatar_file.name = f"avatar_{user_profile.username}{file_extension}"  # Переименовываем файл
                user_profile.avatar = avatar_file

                # Обновляем остальные поля профиля из формы
            user_profile = form.save(commit=False)  # Сохраняем, но не коммитим еще
            user_profile.save()  # Сохраняем профиль
            return redirect('profile')  # Перенаправляем на страницу профиля
    else:
        form = EditProfileForm(instance=user_profile)  # Передаем instance для отображения текущих данных

    return render(request, 'flowers/edit_profile.html', {
        'user': request.user,
        'form': form,  # Теперь передаем уже созданный form
    })

# Просмотр каталога товаров
def catalog(request):
    products = Product.objects.all()
    return render(request, 'flowers/catalog.html', {'products': products})

# Добавление продукта в корзину
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    quantity = request.POST.get('quantity', 1)  # По умолчанию 1, если не указано
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1

    cart = request.session.get('cart', {})

    if str(product.id) in cart:
        cart[str(product.id)] += quantity
    else:
        cart[str(product.id)] = quantity

    request.session['cart'] = cart

    return redirect('catalog')

@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    products = []
    total_price = 0


    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        amount = product.price * quantity  # Вычисляем сумму для каждого товара
        total_price += amount  # Обновляем общую сумму
        products.append({
            'product': product,
            'quantity': quantity,
            'amount': amount  # Добавляем amount в продукты
        })

    # Определяем способ доставки
    delivery_method = request.POST.get('delivery_method', 'pickup')  # Определяем способ доставки, по умолчанию - "pickup" (самовывоз)
    delivery_price = calculate_delivery_price(total_price, delivery_method)  # Расчет стоимости доставки

    context = {
        'products': products,
        'total_price': total_price,
        'delivery_method': delivery_method,
        'delivery_price': delivery_price,
        'total_price_with_delivery': total_price + delivery_price,
    }

    return render(request, 'flowers/cart.html', context)

@login_required
def update_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        action = request.POST.get('action')
        if action == "increase":
            cart[str(product_id)] += 1  # Увеличиваем количество на 1
        elif action == "decrease" and cart[str(product_id)] > 1:
            cart[str(product_id)] -= 1  # Уменьшаем количество на 1
        if cart[str(product_id)] == 0:
            del cart[str(product_id)]  # Удаляем товар из корзины, если количество = 0

    request.session['cart'] = cart
    return redirect('view_cart')  # Перенаправляем на страницу корзины

@login_required
def clear_cart(request):
    if request.method == 'POST':
        request.session['cart'] = {}  # Очищаем корзину
    return redirect('view_cart')  # Перенаправляем на страницу корзины

def get_product(product_id):
    return Product.objects.get(id=product_id)  # Предположим, что у вас есть модель Product

# Расчёт стоимости доставки
def calculate_delivery_price(total_price, delivery_method):
    if delivery_method == 'courier':
        if total_price < 20000:
            return 2000
        elif total_price >= 20000 and total_price < 50000:
            return 1000
        else:
            return 0
    else:
        return 0  # Для самовывоза стоимость доставки 0

# Оформление заказа
@login_required
def order_create(request):
    if request.method == 'POST':
        # Получаем данные из формы
        delivery_method = request.POST.get('delivery_method')
        payment_method = request.POST.get('payment_method')
        address = request.POST.get('address', '')  # Получаем адрес, если он есть
        phone_number = request.POST.get('phone_number', '')  # Получаем телефон, если он есть

        cart = request.session.get('cart', {})

        if not cart:
            messages.info(request, 'Корзина пуста.')
            return redirect('catalog')

        if not request.user.is_authenticated:
            messages.info(request, 'Пожалуйста, войдите в аккаунт для оформления заказа.')
            return redirect('login')  # Перенаправление на страницу входа

        # Создание нового заказа
        order = Order.objects.create(
            user=request.user,
            total_price=0,  # Сумма будет рассчитана позже
            order_date=datetime.now(),
            status='Новый',
            delivery_method=delivery_method,
            delivery_price=0,  # Стоимость доставки будет рассчитана позже
            payment_method=payment_method,
            address=address if delivery_method == 'courier' else None,  # Сохраняем адрес только для курьерской доставки
            phone_number=phone_number if delivery_method == 'courier' else None,  # Сохраняем телефон только для курьерской доставки
        )


        # Получение объектов продуктов на основе идентификаторов
        total_price = 0

        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            amount = product.price * quantity  # Вычисляем сумму для каждого продукта
            OrderItem.objects.create(order=order, product=product, quantity=quantity, amount=amount)
            total_price += amount  # суммируем в общую сумму

        # Сохранение общей суммы в заказе, стоимость доставки и итоговую сумму
        order.total_price = total_price
        order.delivery_price = calculate_delivery_price(total_price, delivery_method)
        order.total_price_with_delivery = order.total_price + order.delivery_price
        order.save()  # Сохраняем заказ с обновленной общей суммой

        # Очищаем корзину, если указано
        if 'clear_cart' in request.POST:
            request.session['cart'] = {}  # Очищаем корзину

        # Перенаправление на страницу с итогами заказа
        return redirect('order_detail', order_id=order.id)

    products = Product.objects.filter(in_stock=True)  # Здесь можете оставить или отфильтровать
    return render(request, 'flowers/order_detail.html', {'products': products})

# Просмотр деталей заказа
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()

    total_price = order.total_price  # Получите общую стоимость заказа
    delivery_method = order.delivery_method  # Получите метод доставки из заказа

    # Теперь вызываем функцию с двумя аргументами
    delivery_price = calculate_delivery_price(total_price, delivery_method)

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': order.total_price,
        'delivery_price': delivery_price,
        'total_price_with_delivery': total_price + delivery_price,
    }
    return render(request, 'flowers/order_detail.html', context)

# Повторение заказа
@login_required
def repeat_order(request, order_id):
    # Извлечение существующего заказа
    existing_order = get_object_or_404(Order, id=order_id)

    # Создание нового заказа
    new_order = Order.objects.create(
        user=existing_order.user,
        total_price=existing_order.total_price,
        order_date=datetime.now(),
        status='Новый',

    )

    # Копирование данных из существующего заказа в новый
    existing_order_items = OrderItem.objects.filter(order=existing_order)
    for item in existing_order_items:
        OrderItem.objects.create(
            order=new_order,
            product=item.product,
            quantity=item.quantity,
            amount=item.amount,
        )

    # Сохранение нового заказа
    new_order.save()

    # Отправка сообщения пользователю
    messages.success(request, 'Заказ успешно повторен!')

    # Перенаправление на страницу с деталями нового заказа
    return redirect('order_detail', order_id=new_order.id)


# Изменение статуса заказа
@csrf_exempt
@require_POST
@login_required
def change_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('id')
        new_status = data.get('status')

    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        return JsonResponse({'message': 'Статус заказа обновлён успешно.'}, status=200)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Заказ не найден.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Просмотр истории заказов
@login_required
def order_history(request):

    sort_order = request.GET.get('sort', 'asc')  # по умолчанию сортируем по убыванию

    if sort_order == 'asc':
        orders = Order.objects.filter(user=request.user).order_by('-order_date')
    else:
        orders = Order.objects.filter(user=request.user).order_by('order_date')

    if not request.user.is_authenticated:
        messages.info(request, 'Пожалуйста, войдите в аккаунт для оформления заказа.')
        return redirect('login')  # Перенаправление на страницу входа
    return render(request, 'flowers/order_history.html', {'orders': orders})

@login_required
def all_orders_history(request):
    # Получаем параметры сортировки и фильтрации
    status_filter = request.GET.get('status', '')  # По умолчанию фильтруем по всем статусам
    print(f"Status filter: {status_filter}")  # Добавьте это для отладки
    sort_order = request.GET.get('sort', 'desc')  # По умолчанию сортируем по убыванию (desc)
    username_filter = request.GET.get('username', '')

    # Получаем даты из параметров запроса
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Запрос для получения заказов
    orders = Order.objects.all()

    # Применяем фильтр по статусу
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Применяем фильтр по имени пользователя, если он задан
    if username_filter:
        orders = orders.filter(user__username__icontains=username_filter)

    if date_from:
        date_from = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'))  # "с"
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        # Преобразуем date_to в datetime и добавляем один день
        date_to_datetime = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        orders = orders.filter(order_date__lt=date_to_datetime)  # Включительно до конца дня



    # Применяем сортировку
    if sort_order == 'asc':
        orders = orders.order_by('order_date')  # Сортировка по возрастанию
    else:
        orders = orders.order_by('-order_date')  # Сортировка по убыванию

    return render(request, 'flowers/all_orders_history.html', {
        'orders': orders,
        'status_filter': status_filter,
        'username_filter': username_filter,
        'sort_order': sort_order,
        'date_from': date_from,
        'date_to': date_to,
    })


# Добавление отзыва
@login_required
def review_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST['rating']
        review_text = request.POST['review_text']
        review = Review.objects.create(user=request.user, product=product, rating=rating, review_text=review_text)
        review.save()
        messages.success(request, 'Ваш отзыв был успешно добавлен!')
        if not request.user.is_authenticated:
            messages.info(request, 'Пожалуйста, войдите в аккаунт для оформления отзыва о продукте.')
            return redirect('login')  # Перенаправление на страницу входа
        return redirect('catalog')
    return render(request, 'flowers/review_create.html', {'product': product})

# Просмотр отзывов о товаре
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', [])
    reviews = Review.objects.filter(product=product)

    # Проверяем, находится ли продукт в корзине
    in_cart = product.id in cart

    return render(request, 'flowers/product_detail.html', {
        'product': product,
        'in_cart': in_cart,
        'reviews': reviews
    })





# Генерация отчета о продажах
@login_required
def generate_sales_report(request):
    if request.method == 'POST':
        # Получаем параметры от формы
        username_filter = request.POST.get('username', '')
        start_date_str = request.POST.get('date_from', '')
        end_date_str = request.POST.get('date_to', '')

        # Проверка наличия значений для дат
        if not start_date_str or not end_date_str:
            # Обработайте ошибку, например, вернув ответ с сообщением об ошибке
            return render(request, 'flowers/generate_sales_report.html', {
                'error': 'Пожалуйста, введите обе даты.',
                'username_filter': username_filter,
                'date_from': start_date_str,
                'date_to': end_date_str,
            })

            # Преобразуем строки в осведомленные временные метки
        start_date = make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)

        # Фильтр продаж на основе дат
        orders = Order.objects.filter(order_date__range=[start_date, end_date])

        # Подсчет total_sales и количества заказов
        total_sales = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        count = orders.count()

        # Собираем все ID заказов в текстовый список
        orders_ids = ', '.join(str(order.id) for order in orders)

        # Сохраняем отчет в таблице Report
        with transaction.atomic():  # Обеспечим целостность данных
            report = Report.objects.create(
                orders=orders_ids,
                total_sales=total_sales,
                count=count,
                start_date=start_date,
                end_date=end_date,
                report_date=datetime.now()
            )



            # Отправляем данные на страницу с отчётом
        return render(request, 'flowers/sales_report.html', {
            'orders': orders,
            'total_sales': total_sales,
            'count': count,
            'username_filter': username_filter,
            'date_from': start_date,
            'date_to': end_date,
            'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
        })

        # Если GET-запрос, заполняем фильтры из URL
    username_filter = request.GET.get('username', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    return render(request, 'flowers/generate_sales_report.html', {
        'username_filter': username_filter,
        'date_from': date_from,
        'date_to': date_to,
    })

# Просмотр списка всех отчётов о продажах
@login_required
def view_sales_reports(request):
    reports = Report.objects.all()
    return render(request, 'flowers/view_sales_reports.html', {'reports': reports})

# Просмотр деталей отчета о продажах
@login_required
def sales_report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, 'flowers/sales_report_detail.html', {
        'report': report,
        'report_id': report_id,
        'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
    })

# Аналитика продаж
@login_required
def sales_analysis(request):
    current_year = datetime.now().year
    year = request.GET.get('year', current_year)
    month = request.GET.get('month', datetime.now().month)

    # Получение продаж по дням за выбранный месяц и год
    total_sales_data = Order.objects.filter(order_date__year=year, order_date__month=month)\
        .annotate(day=F('order_date__day'))\
        .values('day')\
        .annotate(total_sales=Sum('total_price'))\
        .order_by('day')

    # Получение продаж по товарам за месяц
    product_sales_data = OrderItem.objects.filter(order__order_date__year=year, order__order_date__month=month)\
        .values('product__name')\
        .annotate(total_sales=Sum('total_price'), total_quantity=Sum('quantity'))\
        .order_by('product__name')

    # Установите использование "Agg" backend для Matplotlib
    plt.switch_backend('Agg')

    # Создание графика "Продажи по дням месяца"
    days = [data['day'] for data in total_sales_data]
    sales = [data['total_sales'] for data in total_sales_data]

    plt.figure(figsize=(8, 4))
    plt.plot(days, sales, marker = 'o')
    plt.title('Продажи по дням месяца')
    plt.xlabel('Дни месяца')
    plt.ylabel('Общие суммы продаж')
    plt.xticks(np.arange(1, 32, 1))  # Установить метки по оси X от 1 до 31
    plt.grid()

    # Определите путь к директории для сохранения графиков
    sales_directory = os.path.join(settings.MEDIA_ROOT, 'sales/analysis')

    # Проверьте, существует ли директория, если нет - создайте её
    if not os.path.exists(sales_directory):
        os.makedirs(sales_directory)

        # Укажите полный путь для сохранения изображения
    daily_sales_image_path = os.path.join(sales_directory, 'daily_sales.png')

    # Теперь сохраните изображение
    plt.savefig(daily_sales_image_path)
    plt.close()

    # Создание гистограммы "Продажи по товарам"
    products = [product['product__name'] for product in product_sales_data]
    quantities = [product['total_quantity'] for product in product_sales_data]

    plt.figure(figsize=(8, 4))
    plt.bar(products, quantities, color='skyblue')
    plt.title('Продажи по товарам')
    plt.xlabel('Название товара')
    plt.ylabel('Количество в заказах')
    plt.xticks(rotation=45)
    plt.grid(axis='y')

    # Сохраняем изображение
    product_sales_image_path = os.path.join(sales_directory, 'product_sales.png')
    plt.savefig(product_sales_image_path)
    plt.close()

    context = {
        'total_sales_data': total_sales_data,
        'product_sales_data': product_sales_data,
        'years': range(2020, current_year + 1),
        'months': list(calendar.month_name)[1:],  # Список месяцев
        'selected_year': year,
        'selected_month': month,
        'daily_sales_image': os.path.join(settings.MEDIA_URL, 'sales/analysis/daily_sales.png'),
        'product_sales_image': os.path.join(settings.MEDIA_URL, 'sales/analysis/product_sales.png'),
    }

    return render(request, 'flowers/sales_analysis.html', context)