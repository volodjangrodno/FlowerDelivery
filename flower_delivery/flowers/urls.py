from django.urls import path
from . import views
from .views import register, login_view, catalog, order_create, order_detail, product_detail, review_create, generate_sales_report, view_sales_reports

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('catalog/', catalog, name='catalog'),
    path('order/create/', order_create, name='order_create'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', review_create, name='review_create'),
    path('sales/report/generate/', generate_sales_report, name='generate_sales_report'),  # Генерация отчета
    path('sales/reports/', view_sales_reports, name='view_sales_reports'),  # Просмотр отчетов
]


