from database import Base
from sqlalchemy import String, Integer, Column, DateTime
from datetime import datetime
import sqlalchemy

metadata = sqlalchemy.MetaData()


class Photo(Base):
    """
    Структура БД:
    <код запроса>
    <имя сохраненного файла>
    <дата / время регистрации>
    """
    __tablename__ = 'index'
    req_code = Column(Integer, nullable=False)
    name_ph = Column(String(255), primary_key=True)
    date_time = Column(DateTime, default=datetime.now)
