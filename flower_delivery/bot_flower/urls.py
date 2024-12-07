from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('send_order_status_update/<int:order_id>/', views.send_order_status_update, name='send_order_status_update'),
    path('send_order_confirmation/<int:order_id>/', views.send_order_confirmation, name='send_order_confirmation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)