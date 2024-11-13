from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Мои заказы", callback_data="my_orders"),
     InlineKeyboardButton(text="Аналитика", callback_data="analytics")]
])

async def get_orders_list(orders):
    keyboard = InlineKeyboardMarkup()
    for order in orders:
        keyboard.add(InlineKeyboardButton(
            text=f'Заказ №{order.id} от {order.order_date} на сумму {order.total_price}',
            callback_data=f"order_details:{order.id}"
        ))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_start"))
    return keyboard