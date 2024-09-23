from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import os
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Sum
from .forms import CustomUserCreationForm, EditProfileForm
from .models import Product, Order, Review, Report, SaleReport, CustomUser, OrderItem, EditProfile
from django.utils import timezone
from django.utils.timezone import make_aware
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
            form.save()

            return redirect('login')
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
    user_profile = EditProfile.objects.get(user=request.user)
    return render(request, 'flowers/profile.html', {'user': request.user, 'profile': user_profile})

# Редактирование профиля пользователя
@login_required
def edit_profile(request):
    user_profile, created = EditProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_profile.username = request.POST['username']
        user_profile.email = request.POST['email']
        if 'avatar' in request.FILES:
            # Сохраните аватар с новым именем
            avatar_file = request.FILES['avatar']
            file_extension = os.path.splitext(avatar_file.name)[1]
            avatar_file.name = f"avatar_{user_profile.username}{file_extension}"  # Переименовываем файл
            user_profile.avatar = avatar_file
        user_profile.first_name = request.POST['first_name']
        user_profile.last_name = request.POST['last_name']
        user_profile.save()
        return redirect('profile')
    return render(request, 'flowers/edit_profile.html',
                  {'user': request.user, 'form': EditProfileForm(instance=user_profile)})

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

    context = {
        'products': products,
        'total_price': total_price,
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

# Оформление заказа
@login_required
def order_create(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})

        if not cart:
            messages.info(request, 'Корзина пуста.')
            return redirect('catalog')

        if not request.user.is_authenticated:
            messages.info(request, 'Пожалуйста, войдите в аккаунт для оформления заказа.')
            return redirect('login')  # Перенаправление на страницу входа

        # Создание нового заказа
        order = Order.objects.create(user=request.user)

        # Получение объектов продуктов на основе идентификаторов
        total_price = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            amount = product.price * quantity  # Вычисляем сумму для каждого продукта
            OrderItem.objects.create(order=order, product=product, quantity=quantity, amount=amount)
            total_price += amount  # суммируем в общую сумму

        # Сохранение общей суммы в заказе
        order.total_price = total_price
        order.save()  # Сохраняем заказ с обновленной общей суммой

        # Очищаем корзину, если указано
        if 'clear_cart' in request.POST:
            request.session['cart'] = {}  # Очищаем корзину

        # Перенаправление на страницу с итогами заказа
        return redirect('order_detail', order_id=order.id, total_price=total_price)

    products = Product.objects.all()  # Здесь можете оставить или отфильтровать
    return render(request, 'flowers/order_detail.html', {'products': products})

# Просмотр деталей заказа
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.order_items.all()


    return render(request, 'flowers/order_detail.html', {'order': order, 'order_items': order_items})

# Повторение заказа
@login_required
def repeat_order(request, order_id):
    # Извлечение существующего заказа
    existing_order = get_object_or_404(Order, id=order_id)

    # Создание нового заказа
    new_order = Order.objects.create(
        user=existing_order.user,
        total_price=existing_order.total_price,
        order_date=datetime.datetime.now(),
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
    sort_order = request.GET.get('sort', 'desc')  # По умолчанию сортируем по убыванию (desc)
    username_filter = request.GET.get('username', '')

    # Получаем даты из параметров запроса
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Запрос для получения заказов
    orders = Order.objects.all()

    # Применяем фильтр по имени пользователя, если он задан
    if username_filter:
        orders = orders.filter(user__username__icontains=username_filter)

    if date_from:
        orders = orders.filter(order_date__gte=date_from)  # "с"
    if date_to:
        orders = orders.filter(order_date__lte=date_to)  # "по"

    # Применяем сортировку
    if sort_order == 'asc':
        orders = orders.order_by('order_date')  # Сортировка по возрастанию
    else:
        orders = orders.order_by('-order_date')  # Сортировка по убыванию

    return render(request, 'flowers/all_orders_history.html', {
        'orders': orders,
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
def all_orders_history(request):
    # Получаем параметры фильтрации и сортировки
    sort_order = request.GET.get('sort', 'desc')
    username_filter = request.GET.get('username', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Запрос для получения заказов
    orders = Order.objects.all()

    # Применяем фильтрацию
    if username_filter:
        orders = orders.filter(user__username__icontains=username_filter)

        # Проверяем и применяем фильтрацию по дате "С"
    if date_from:
        orders = orders.filter(order_date__gte=date_from)  # Включительно

        # Проверяем и применяем фильтрацию по дате "По"
        if date_to:
            # Преобразуем date_to в datetime и добавляем один день
            date_to_datetime = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            orders = orders.filter(order_date__lt=date_to_datetime)  # Включительно до конца дня

    # Сортируем заказы
    orders = orders.order_by('-order_date' if sort_order == 'desc' else 'order_date')

    # Количество отфильтрованных заказов
    sales_count = orders.count()  # Подсчет количества заказов

    return render(request, 'flowers/all_orders_history.html', {
        'orders': orders,
        'username_filter': username_filter,
        'sort_order': sort_order,
        'date_from': date_from,
        'date_to': date_to,
        'sales_count': sales_count,  # Передаем количество в контексте
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
def sales_report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, 'flowers/sales_report_detail.html', {
        'report': report,
        'report_id': report_id,
        'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
    })