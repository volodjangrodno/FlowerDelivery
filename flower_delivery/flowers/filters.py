from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает два числа."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0  # Возвращаем 0 при ошибке