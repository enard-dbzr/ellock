import os
from random import randint
from datetime import datetime
from threading import Thread
import telebot
from telebot import types, formatting
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import exc

from ells.settings import get_settings
from ells.models import consts
from ells.tools import Eventer
from ells import hardware
from ells.models import db_session
from ells.models.users import User

bot = telebot.TeleBot(os.environ.get("ELL_TG_TOKEN"), threaded=True)

open_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
btn_open = types.KeyboardButton("Открыть")
open_markup.add(btn_open)

keyboard_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
keyboard_markup.add(*([str(n) for n in range(1, 10)] + ["Отмена", "0"]),
                    row_width=3)

settings = get_settings()
events: Eventer = None

crossquery_settings = {}


@bot.message_handler(commands=["start", "help"])
def start_handler(message):
    bot.reply_to(message, "Начало",
                 reply_markup=open_markup)


@bot.message_handler(func=lambda m: m.text.lower() == "открыть")
def open_handler(message: telebot.types.Message):
    db = db_session.create_session()

    user = db.query(User).filter_by(tg_id=message.from_user.id).first()
    if user is None or not user.is_known:
        if user is None:
            user = User(tg_id=message.from_user.id,
                        display_name=message.from_user.full_name)

            db.add(user)
            db.commit()
            db.refresh(user)

        events.create_event(consts.NEW_ACCESS, user.id)
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
    events.create_event(consts.OPEN, user.id)
    return bot.send_message(message.chat.id, "Открыто",
                            reply_markup=open_markup)


@bot.message_handler(func=lambda m: m.text.lower() == "отмена")
def cancel_handler(message):
    return bot.send_message(message.chat.id, "Ок",
                            reply_markup=open_markup)


def confirm_step(message, key):
    db = db_session.create_session()
    user = db.query(User).filter_by(tg_id=message.from_user.id,
                                    is_known=True).first()

    if message.text.lower() == "отмена":
        return bot.send_message(message.chat.id, "Ок",
                                reply_markup=open_markup)

    if str(key) != message.text.lower():
        return bot.send_message(message.chat.id, "Отказано",
                                reply_markup=open_markup)

    hardware.open()
    events.create_event(consts.OPEN, user.id)
    return bot.send_message(message.chat.id, "Открыто",
                            reply_markup=open_markup)


def notif_handler(event_type, user_id):
    db = db_session.create_session()
    target = db.query(User).get(user_id)
    target_name = formatting.hlink(
        target.display_name, "tg://user?id={}".format(target.tg_id))

    users = db.query(User).filter(
        User.notifications.contains(";{};".format(event_type))).all()

    msg = admin_msg = None
    markup = admin_markup = None
    if event_type == consts.MESSAGE:
        msg = "Новое сообщение от {username}"
    elif event_type == consts.NEW_ACCESS:
        msg = "Запрос доступа от {username}"

        admin_markup = InlineKeyboardMarkup()
        admin_markup.add(InlineKeyboardButton("ДА", callback_data="acc_yes"),
                         InlineKeyboardButton("НЕТ", callback_data="acc_no"))
        admin_msg = "Запрос доступа от {username}. Разрешить доступ?"
    elif event_type == consts.OPEN:
        msg = "Дверь открыта {username}"

    for user in users:
        if user.id != user_id:
            if admin_msg and user.is_admin:
                cur_msg = admin_msg
                cur_markup = admin_markup
            else:
                cur_msg = msg
                cur_markup = markup

            resp = bot.send_message(user.tg_id,
                                    cur_msg.format(username=target_name),
                                    parse_mode="HTML",
                                    reply_markup=cur_markup)
            crossquery_settings[resp.id] = {"def_msg": msg.format(username=target_name),
                                            "user_id": user_id}


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    db = db_session.create_session()

    if call.message.id not in crossquery_settings:
        bot.edit_message_reply_markup(call.from_user.id,
                                      call.message.id,
                                      reply_markup=None)
        return bot.answer_callback_query(call.id, "Ошибка")

    args = crossquery_settings.pop(call.message.id)

    bot.edit_message_text(args["def_msg"], call.from_user.id, call.message.id,
                          reply_markup=None, parse_mode="HTML")

    if db.query(User).filter_by(tg_id=call.from_user.id, is_admin=True).count() == 0:
        return bot.answer_callback_query(call.id, "Отсутсвуют права на выполнение данной операции")

    if call.data == "acc_yes":
        db.query(User).get(args["user_id"]).is_known = True
        db.commit()
        return bot.answer_callback_query(call.id, "Доступ пользователю разрешен")

    db.query(User).get(args["user_id"]).is_known = False
    db.commit()
    return bot.answer_callback_query(call.id, "Доступ пользователю запрещен")


def start_bot(eventer):
    def poller():
        while True:
            try:
                bot.polling()
            except Exception:
                pass

    global events
    events = eventer
    events.set_notif_handler(notif_handler)

    bot_th = Thread(target=poller, daemon=True)
    bot_th.start()
    return bot
