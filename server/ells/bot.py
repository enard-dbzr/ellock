import os
from random import randint
from datetime import datetime
from threading import Thread
import telebot
from telebot import types
from sqlalchemy import exc

from ells.settings import get_settings
from ells import hardware
from ells.models import db_session
from ells.models.users import User

TOKEN = "2070286205:AAEXhK5B9UtmplDq60Vwb-L0d7MEnLfEBdk"
bot = telebot.TeleBot(TOKEN, threaded=True)

open_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
btn_open = types.KeyboardButton("Открыть")
open_markup.add(btn_open)

keyboard_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
keyboard_markup.add(*([str(n) for n in range(1, 10)] + ["Отмена", "0"]),
                    row_width=3)

settings = get_settings()


@bot.message_handler(commands=["start", "help"])
def start_handler(message):
    bot.reply_to(message, "Начало",
                 reply_markup=open_markup)


@bot.message_handler(func=lambda m: m.text.lower() == "открыть")
def open_handler(message):
    db = db_session.create_session()

    user = db.query(User).filter_by(tg_id=message.from_user.id,
                                    is_known=True).first()

    if user is None:
        try:
            new_user = User(tg_id=message.from_user.id)
            db.add(new_user)
            db.commit()
        except exc.IntegrityError:
            pass

        return bot.send_message(message.chat.id, "Запрос для этого аккаунта отправлен...",
                                reply_markup=open_markup)

    if datetime.now().timestamp() - message.date > settings["security"]["bot_timeout"]:
        return bot.reply_to(message, "Таймаут...",
                            reply_markup=open_markup)

    if settings["protection"]["type"] == "single":
        key = settings["protection"]["key"]
        msg = bot.send_message(
            message.chat.id,
            "Подтвердите действие: выберите необходимую цифру",
            reply_markup=keyboard_markup)

        return bot.register_next_step_handler(msg, confirm_step, key)
    elif settings["protection"]["type"] == "single_random":
        key = randint(0, 9)
        msg = bot.send_message(
            message.chat.id,
            "Подтвердите действие: выберите цифру ___{}___".format(key),
            parse_mode="Markdown",
            reply_markup=keyboard_markup)

        return bot.register_next_step_handler(msg, confirm_step, key)
    elif settings["protection"]["type"] == "text":
        key = settings["protection"]["key"]
        msg = bot.send_message(
            message.chat.id,
            "Подтвердите действие: введите необходимый текст")

        return bot.register_next_step_handler(msg, confirm_step, key)
    elif settings["protection"]["type"] == "random_num":
        key = randint(1000, 9999)
        msg = bot.send_message(
            message.chat.id,
            "Подтвердите действие: введите число ___{}___".format(key),
            parse_mode="Markdown")

        return bot.register_next_step_handler(msg, confirm_step, key)

    hardware.open()
    return bot.send_message(message.chat.id, "Открыто",
                            reply_markup=open_markup)


@bot.message_handler(func=lambda m: m.text.lower() == "отмена")
def cancel_handler(message):
    return bot.send_message(message.chat.id, "Ок",
                            reply_markup=open_markup)


def confirm_step(message, key):
    if message.text.lower() == "отмена":
        return bot.send_message(message.chat.id, "Ок",
                                reply_markup=open_markup)

    if str(key) != message.text.lower():
        return bot.send_message(message.chat.id, "Отказано",
                                reply_markup=open_markup)

    hardware.open()
    return bot.send_message(message.chat.id, "Открыто",
                            reply_markup=open_markup)


def start_bot():
    def poller():
        while True:
            try:
                bot.polling()
            except Exception:
                pass

    bot_th = Thread(target=poller, daemon=True)
    bot_th.start()
