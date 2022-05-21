from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData

engine = create_engine("postgresql://postgres:postgres@localhost/postgres", echo=True)
                        # Где postgres - пароль от личной БД(2), а postgres - название БД(1)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)
