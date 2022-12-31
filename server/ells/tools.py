from datetime import datetime
from telebot import TeleBot
from telebot import formatting

from ells.models import db_session
from ells.models.users import User
from ells.models.events import Event
from ells.models import consts


class Eventer:
    def __init__(self) -> None:
        self.send_notif = None

    def set_notif_handler(self, handler):
        self.send_notif = handler

    def create_event(self, event_type, user_id):
        db = db_session.create_session()
        new_event = Event(event_type=event_type, user_id=user_id,
                          datetime=datetime.now())
        db.add(new_event)
        db.commit()

        self.send_notif(event_type, user_id)
