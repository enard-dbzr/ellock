from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase, create_session
from sqlalchemy_serializer import SerializerMixin


class Event(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    datetime = Column(DateTime)