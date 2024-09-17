from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Product, Order, Review, Report, SaleReport, CustomUser, OrderItem, EditProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff']

# Register your models here.
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Report)
admin.site.register(SaleReport)
admin.site.register(EditProfile)