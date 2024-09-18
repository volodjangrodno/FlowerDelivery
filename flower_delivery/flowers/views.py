from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import os
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime
from django.utils import timezone
from django.db.models import Sum
from .forms import CustomUserCreationForm, EditProfileForm
from .models import Product, Order, Review, Report, SaleReport, CustomUser, OrderItem, EditProfile
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
    orders = Order.objects.filter(user=request.user)
    if not request.user.is_authenticated:
        messages.info(request, 'Пожалуйста, войдите в аккаунт для оформления заказа.')
        return redirect('login')  # Перенаправление на страницу входа
    return render(request, 'flowers/order_history.html', {'orders': orders})

@login_required
def all_orders_history(request):
    orders = Order.objects.all()
    return render(request, 'flowers/all_orders_history.html', {'orders': orders})

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
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        sales = SaleReport.objects.filter(sale_date__range=[start_date, end_date])
        total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        return render(request, 'flowers/sales_report.html', {'sales': sales, 'total_sales': total_sales})
    return render(request, 'flowers/generate_sales_report.html')

# Просмотр всех отчетов о продажах
@login_required
def view_sales_reports(request):
    reports = SaleReport.objects.all()
    return render(request, 'flowers/view_sales_reports.html', {'reports': reports})
