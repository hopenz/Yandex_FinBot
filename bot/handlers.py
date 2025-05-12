import logging
from datetime import datetime
from aiogram import F, types
from aiogram.filters import Command
from bot.config import connect_to_db, VERBOSE_LOG
from bot.utils import category_keyboard

logger = logging.getLogger()
if VERBOSE_LOG:
    logger.setLevel(logging.INFO)

pending_expenses = {}

def register_handlers(dp):
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, context):
        try:
            conn = connect_to_db(context)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (message.from_user.id,))
            cur.execute("INSERT INTO user_balances (user_id, balance) VALUES (%s, 0) ON CONFLICT DO NOTHING", (message.from_user.id,))
            conn.commit(); cur.close(); conn.close()

            await message.answer("Вы успешно зарегистрированы!")
            await message.answer_photo("https://storage.yandexcloud.net/bot-storage-petrushina/images/image1.jpg")
        except Exception as e:
            logger.error(f"/start error: {e}")
            await message.answer("Ошибка подключения к базе данных.")

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        await message.answer(
            "Доступные команды:\n"
            "/start — регистрация\n"
            "/help — справка\n"
            "/balance — текущий баланс\n"
            "/expenses — список расходов\n"
            "/incomes — список доходов\n\n"
            "Добавление операций:\n"
            "+ <сумма> <описание> — доход\n"
            "- <сумма> <описание> (с выбором категории)"
        )

    @dp.message(Command("balance"))
    async def cmd_balance(message: types.Message, context):
        try:
            conn = connect_to_db(context)
            cur = conn.cursor()
            cur.execute("SELECT balance FROM user_balances WHERE user_id = %s", (message.from_user.id,))
            row = cur.fetchone(); cur.close(); conn.close()
            await message.answer(f"Ваш текущий баланс: {row[0]:.2f} ₽" if row else "Баланс не найден.")
        except Exception as e:
            logger.error(f"/balance error: {e}")
            await message.answer("Ошибка при получении баланса.")

    @dp.message(Command("expenses"))
    async def cmd_expenses(message: types.Message, context):
        try:
            conn = connect_to_db(context)
            cur = conn.cursor()
            cur.execute("SELECT amount, description, category, created_at FROM expenses WHERE user_id = %s ORDER BY created_at DESC", (message.from_user.id,))
            rows = cur.fetchall(); cur.close(); conn.close()
            if not rows:
                await message.answer("У вас нет расходов.")
            else:
                msg = "Ваши расходы:\n\n" + "\n".join(
                    f"{created:%d.%m.%Y}  {amount:.2f} ₽  {desc}  {category}" for amount, desc, category, created in rows
                )
                await message.answer(msg)
        except Exception as e:
            logger.error(f"/expenses error: {e}")
            await message.answer("Ошибка при получении расходов.")

    @dp.message(Command("incomes"))
    async def cmd_incomes(message: types.Message, context):
        try:
            conn = connect_to_db(context)
            cur = conn.cursor()
            cur.execute("SELECT amount, description, created_at FROM incomes WHERE user_id = %s ORDER BY created_at DESC", (message.from_user.id,))
            rows = cur.fetchall(); cur.close(); conn.close()
            if not rows:
                await message.answer("У вас нет доходов.")
            else:
                msg = "Ваши доходы:\n" + "\n".join(
                    f"{created:%d.%m.%Y}: {amount:.2f} ₽ — {desc}" for amount, desc, created in rows
                )
                await message.answer(msg)
        except Exception as e:
            logger.error(f"/incomes error: {e}")
            await message.answer("Ошибка при получении доходов.")

    @dp.message(F.text.regexp(r"^[\+\-]\s*\d+(\.\d+)?"))
    async def handle_operation(message: types.Message, context):
        text = message.text.strip()
        is_income = text.startswith("+")
        amount = float(text[1:].strip().split()[0])
        desc = " ".join(text[1:].strip().split()[1:]).strip() or "Без описания"

        if is_income:
            try:
                conn = connect_to_db(context)
                cur = conn.cursor()
                cur.execute("INSERT INTO incomes (user_id, amount, description) VALUES (%s, %s, %s)", (message.from_user.id, amount, desc))
                cur.execute("UPDATE user_balances SET balance = balance + %s WHERE user_id = %s", (amount, message.from_user.id))
                conn.commit(); cur.close(); conn.close()
                await message.answer(f"Доход {amount:.2f} ₽ добавлен: {desc}")
            except Exception as e:
                logger.error(f"Ошибка добавления дохода: {e}")
                await message.answer("Не удалось добавить доход.")
        else:
            pending_expenses[message.from_user.id] = f"{amount},{desc}"
            await message.answer("Выберите категорию расхода:", reply_markup=category_keyboard())

    @dp.callback_query(F.data.regexp(r"^cat:"))
    async def category_selected(callback: types.CallbackQuery, context):
        user_id = callback.from_user.id
        category = callback.data.split(":", 1)[1]
        exp = pending_expenses.pop(user_id, None)

        if not exp:
            await callback.answer("Нет ожидающего расхода.")
            return

        amount, desc = exp.split(",", 1)
        try:
            conn = connect_to_db(context)
            cur = conn.cursor()
            cur.execute("INSERT INTO expenses (user_id, amount, description, category) VALUES (%s, %s, %s, %s)",
                        (user_id, amount, desc, category))
            cur.execute("UPDATE user_balances SET balance = balance - %s WHERE user_id = %s", (amount, user_id))
            conn.commit(); cur.close(); conn.close()
            await callback.message.answer(f"Расход {amount} ₽ добавлен в категорию: {category}")
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка при добавлении расхода: {e}")
            await callback.message.answer("Ошибка при добавлении расхода.")
            await callback.answer("Ошибка")