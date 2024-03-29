from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ("-hashed_password", )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    display_name = Column(String)
    tg_id = Column(Integer, unique=True)
    hashed_password = Column(String)

    is_admin = Column(Boolean, default=False)
    is_known = Column(Boolean, default=False)

    notifications = Column(String)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
