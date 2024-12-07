from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Мои заказы", callback_data="my_orders"),
     InlineKeyboardButton(text="Аналитика", callback_data="analytics")]
])

back_to_start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="back_to_start")]
])

async def get_orders_list(orders):
    list_orders_keyboard = InlineKeyboardMarkup()
    for order in orders:
        list_orders_keyboard.add(InlineKeyboardButton(
            text=f"Заказ №{order.id} от {order.order_date.strftime('%d-%m-%Y %H:%M')} на сумму {order.total_price_with_delivery} руб.",
            callback_data=f"order_details:{order.id}"
        ))
    list_orders_keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_start"))
    return list_orders_keyboard