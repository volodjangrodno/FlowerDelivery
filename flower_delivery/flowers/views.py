from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Order
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'flowers/home.html')  # Убедитесь, что у вас есть шаблон home.html


# Регистрация пользователя
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('catalog')
    else:
        form = UserCreationForm()
    return render(request, 'flowers/register.html', {'form': form})

# Авторизация пользователя
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('catalog')
    return render(request, 'flowers/login.html')

# Просмотр каталога товаров
def catalog(request):
    products = Product.objects.all()
    return render(request, 'flowers/catalog.html', {'products': products})

# Оформление заказа
@login_required
def order_create(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('products')
        order = Order.objects.create(user=request.user)
        order.products.set(product_ids)
        order.save()
        return redirect('order_detail', order_id=order.id)
    products = Product.objects.all()
    return render(request, 'flowers/order_create.html', {'products': products})

# Просмотр деталей заказа
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'flowers/order_detail.html', {'order': order})

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
        return redirect('catalog')
    return render(request, 'flowers/review_create.html', {'product': product})

# Просмотр отзывов о товаре
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    return render(request, 'flowers/product_detail.html', {'product': product, 'reviews': reviews})

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
