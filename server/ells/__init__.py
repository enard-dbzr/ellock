import os
import json

from ells import settings
from ells.tools import Eventer

from ells.models import db_session
from ells.models.users import User


def run_app():
    first_run()

    settings.load_settings()
    db_session.global_init("database/database.db")
    eventer = Eventer()

    from ells.web import app, socketio
    from ells.hardware import detect_device
    from ells.bot import start_bot
    from ells.api import create_api

    detect_device()
    bot = start_bot(eventer)
    create_api(app)

    socketio.run(app, "0.0.0.0", debug=True, use_reloader=False)


def first_run():
    if not os.path.exists("settings.json"):
        settings.create_settings()
