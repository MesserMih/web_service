from database import Base, engine
from model import Photo

print("Creating database ....")

Base.metadata.create_all(engine)
