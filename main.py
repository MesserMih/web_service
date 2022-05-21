import os
import uvicorn
import uuid
import model
from fastapi import FastAPI, UploadFile, Path
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from database import SessionLocal
from pathlib import Path
from sqlalchemy.orm import Session
from database import Base, engine
from functions import *

tags_metadata = [
    {
        "name": "requests",
        "description": "Тестовое задание для стажировки в Гринатоме"
    }
]

app = FastAPI(
    title="Web service by Oznobikhin Mikhail",
    version="1.0.0",
    openapi_tags=tags_metadata
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/token", tags=["requests"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Запрос POST для авторизации пользователя"""
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.put("/frame/", tags=["requests"])
async def upload_photos(image: List[UploadFile], db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_active_user)):
    """
    Запрос PUT

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

    if not len(image):
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="no images uploaded")

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

    # Сохранение передаваемых изображений в директории /data/ и в базе данных
    for elem in range(0, len(image)):
        content = await image[elem].read()  # Переменная содержания изображения
        new_name = (str(uuid.uuid4()) + ".jpg")  # Имена фотографий, отображемых в папке /data/  НО НЕ ПУТЬ ДО НЕЁ!
        path_photo = os.path.join(path, new_name)  # Путь до фотографии вместе с её именем
        save_file(path_photo, content)  # Создание фотографий в директории /data/

        new_photo = model.Photo(
            req_code=code_count,
            name_ph=new_name,
            date_time=datetime.now()
        )
        db.add(new_photo)
        db.commit()
    return {"status_code": status.HTTP_200_OK, "detail": "Successfully uploaded"}


@app.get('/frame/{id}', response_model=List[Photo], status_code=status.HTTP_200_OK, tags=["requests"])
async def get_photos_by_id(code_in: int, db: Session = Depends(get_db)):
    """
    Запрос GET

    Функция принимает код запроса и возвращает список изображений, соответсвующих коду запроса
    """
    out = db.query(model.Photo).filter(model.Photo.req_code == code_in).all()
    return out


@app.delete('/frame/{id}', status_code=status.HTTP_200_OK, tags=["requests"])
def delete_photos_by_id(id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_active_user)):
    """
    Запрос DELETE

    Функция принимает код запроса и удаляет все изображения и информацию об этих изображениях в БД,
    связанные с кодом запроса
    """
    out = db.query(model.Photo).filter(model.Photo.req_code == id).all()
    if not out:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="photos not found")

    photo_names = [out[elem].name_ph for elem in range(len(out))]

    path_to_photos = [next(Path(os.getcwd()).rglob(elem)) for elem in photo_names]

    for elem in path_to_photos:
        os.remove(elem)

    photos_to_delete = db.query(model.Photo).filter(model.Photo.req_code == id).delete()
    if not photos_to_delete:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="resource not found")

    db.commit()

    return {"status_code": status.HTTP_200_OK, "detail": "Successfully deleted"}


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    uvicorn.run("main:app", reload=True)
