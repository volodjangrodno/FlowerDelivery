from aiogram import types

async def cmd_sales_report(message: types.Message, period: str):
    if message.from_user.role != 'admin':
        await message.answer("У вас нет прав на выполнение этой команды.")
        return

    report = get_sales_report(period)
    await message.answer(report)