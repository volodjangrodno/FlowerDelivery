from django.apps import AppConfig
from .filters import *

class FlowersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flowers'
