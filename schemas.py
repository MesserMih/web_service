from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Photo(BaseModel):
    req_code: int
    name_ph: str
    date_time: datetime

    class Config:
        orm_mode = True


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str
