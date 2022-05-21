from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData

engine = create_engine("postgresql://postgres:postgres@localhost/postgres", echo=True)
                        # Где Messer0Mih - пароль от личной БД, а postgres - название БД

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)
