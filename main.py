import json
import os
import uvicorn
from fastapi import FastAPI, status, HTTPException, UploadFile, Path, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import uuid
import model
from database import SessionLocal
from datetime import datetime
from pathlib import Path
import hashlib


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Photo(BaseModel):
    req_code: int
    name_ph: str
    date_time: datetime

    class Config:
        orm_mode = True


"""
Мнимая база данных пользователей

Здесь введено 2 пользователя:
greenatom - Активный пользователь
mihail - Неактивный пользователь
"""
users_db = {
    "greenatom": {
        "username": "greenatom",
        "hashed_password": "1a1dc91c907325c69271ddf0c944bc72",  # Пароль: pass
        "disabled": False,
    },
    "mihail": {
        "username": "mihail",
        "hashed_password": "c1572d05424d0ecb2a65ec6a82aeacbf",  # Пароль: pass2
        "disabled": True,
    },
}


def hash_password(password: str):
    # Пароль хэшируется с помощью метода md5
    return hashlib.md5(password.encode()).hexdigest()


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


def get_user(data_base, username: str):
    if username in data_base:
        user_dict = data_base[username]
        return UserInDB(**user_dict)


def decode_token(token):
    user = get_user(users_db, token)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Функция авторизации пользователя
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


db = SessionLocal()


def save_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)


@app.put("/frame/")
async def create_photo(image: List[UploadFile], current_user: User = Depends(get_current_active_user)):
    """
    Метод PUT

    Метод принимает от 1 до 15 фотографий в формате jpeg.
    Функция сохраняет переданные изображения
    в директорию /data/<YYYYMMDD>/<GUID>.jpg и фиксирует в базе данных
    в таблице 'inbox'
    """
    out = db.query(model.Photo).all()
    if not out:
        code_count = 0
    else:
        code_count = max([out[elem].req_code for elem in range(0, len(out))])
    code_count += 1
    print(type(image[0]))
    if len(image) == 0:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="no images")

    if len(image) > 15:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="too much images")

    for i in range(0, len(image)):
        if not (os.path.splitext(image[i].filename)[1] == ('.jpg' or '.JPG' or '.JPEG' or '.jpeg')):
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="media type not supported")

    # Создание директорий, в которые будут загружаться изображения и определение путей для фотографий
    directory = datetime.today().strftime("%Y%m%d")
    parent_dir = "data"
    path = os.path.join(parent_dir, directory)
    try:
        os.mkdir(parent_dir)
    except FileExistsError:
        print('Directory not created.')
    try:
        os.mkdir(path)
    except FileExistsError:
        print('Directory not created.')

    # Сохранение передаваемых изображений в директории /data/
    # и в базе данных
    for elem in range(0, len(image)):
        content = await image[elem].read()  # Переменная содержания изображения
        new_name = (
                str(uuid.uuid4()) + ".jpg")  # Имя фотографий, отображемых в папке /data/  НО НЕ ПУТЬ ДО НЕЁ!
        path_photo = os.path.join(path, new_name)  # Путь до фотографии вместе с её именем
        save_file(path_photo, content)  # Создание фотографий в директории /data/

        new_photo = model.Photo(
            req_code=code_count,
            name_ph=new_name,
            date_time=datetime.now()
        )
        db.add(new_photo)
        db.commit()


@app.get('/frame/{code_in}', response_model=List[Photo], status_code=status.HTTP_200_OK)
async def read_photo(code_in: int):
    """
    Метод GET

    Функция принимает код запроса и возвращает список изображений, соответсвующих коду запроса
    """
    out = db.query(model.Photo).filter(model.Photo.req_code == code_in).all()
    return out


@app.delete('/frame/{code_in}', response_model=List[Photo], status_code=status.HTTP_200_OK)
def delete_photo(code_in: int, current_user: User = Depends(get_current_active_user)):
    """
    Метод DELETE

    Функция принимает код запроса и удаляет все изображения и информацию об этих изображениях в БД,
    связанные с кодом запроса
    """
    out = db.query(model.Photo).filter(model.Photo.req_code == code_in).all()
    photo_names = [out[elem].name_ph for elem in
                   range(0, len(out))]  # Выражение определяющее название нужных фотографий

    path_to_photos = [next(Path(os.getcwd()).rglob(elem)) for elem in photo_names]

    [os.remove(elem) for elem in path_to_photos]

    photos_to_delete = db.query(model.Photo).filter(model.Photo.req_code == code_in).delete()
    if not photos_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resource not found")

    db.commit()


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
