import os

from flask import Flask, redirect, render_template, request
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_socketio import SocketIO

from ells.bot import bot
from ells.settings import get_settings, update_settings

from ells.models import db_session
from ells.models.users import User
from ells.models.users_forms import RegisterForm, LoginForm
from ells.models.settings_forms import SettingsForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)

settings = get_settings()


@login_manager.user_loader
def load_user(user_id):
    db = db_session.create_session()
    return db.query(User).get(user_id)


@app.route("/", methods=["GET", "POST"])
def index():
    db = db_session.create_session()

    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user = User(username=register_form.username.data,
                    is_admin=True, is_known=True)
        user.set_password(register_form.passwd.data)

        db.add(user)
        db.commit()
        db.refresh(user)

        login_user(user)

    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.query(User).filter_by(
            username=login_form.username.data.lower(), is_admin=True).first()
        if user and user.check_password(login_form.passwd.data):
            login_user(user)
            return redirect("/")

    admin = db.query(User).filter_by(is_admin=True).first()
    if admin is None:
        return render_template("registration.html", form=register_form)

    if not current_user.is_authenticated:
        return render_template("login.html", form=login_form)

    # users = []
    # for u in db.query(User).all():
    #     users.append(u.to_dict())
        # if u.tg_id:
        #     tg_u = bot.get_chat_member(u.tg_id, u.tg_id)
        #     u_json = {}
        #     u_json["id"] = u.tg_id
        #     u_json["username"] = tg_u.user.username
        #     u_json["first_name"] = tg_u.user.first_name
        #     u_json["last_name"] = tg_u.user.last_name
        #     u_json["is_known"] = u.is_known
        #     users.append(u_json)

    return render_template("index.html", users=db.query(User).all())


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    form = SettingsForm(protection_type=settings["protection"]["type"],
                        protection_key=settings["protection"]["key"],
                        bot_timeout=settings["security"]["bot_timeout"])

    if form.validate_on_submit():
        settings["protection"]["type"] = form.protection_type.data
        settings["protection"]["key"] = form.protection_key.data

        settings["security"]["bot_timeout"] = form.bot_timeout.data

        update_settings()

    return render_template("settings.html", form=form)


@socketio.on("accept_tg")
def accept_tg(tg_id):
    if current_user.is_authenticated:
        db = db_session.create_session()
        user = db.query(User).filter_by(tg_id=tg_id).first()
        user.is_known = True
        db.commit()

    socketio.emit("refresh")


@socketio.on("reject_tg")
def accept_tg(tg_id):
    if current_user.is_authenticated:
        db = db_session.create_session()
        user = db.query(User).filter_by(tg_id=tg_id).first()
        user.is_known = False
        db.commit()

    socketio.emit("refresh")
