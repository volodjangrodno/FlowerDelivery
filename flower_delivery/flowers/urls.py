from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('catalog/', views.catalog, name='catalog'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),  # Новое правило для очистки корзины
    path('cart/', views.view_cart, name='view_cart'),
    path('order/create/', views.order_create, name='order_create'),
    path('order/history/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.review_create, name='review_create'),
    path('sales/report/generate/', views.generate_sales_report, name='generate_sales_report'),  # Генерация отчета
    path('sales/reports/', views.view_sales_reports, name='view_sales_reports'),  # Просмотр отчетов
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
