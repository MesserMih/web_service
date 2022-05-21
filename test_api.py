from fastapi import HTTPException, status, Depends
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from main import app, login, users_db
import os


client = TestClient(app)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
user_dict = users_db.get("greenatom")


# Тест запроса PUT при загрузке от 1 до 15 файлов (2 в частом случае)
def test_put_main_1ph():
    full_test_path = os.path.join('files_for_tests', 'test_ph.jpg')
    image = [('image', open(full_test_path, 'rb')), ('image', open(full_test_path, 'rb'))]
    response = client.put(
        "/frame/",
        files=image,
        headers={'Authorization': f'Bearer {user_dict["username"]}'}
    )
    print(response.headers)
    assert response.status_code == 200


# Тест метода PUT в случае, когда никакой файл не подаётся на вход метода
def test_put_main_0ph():
    image = []
    response = client.put(
        "/frame/",
        files=image,
        headers={'Authorization': f'Bearer {user_dict["username"]}'}
    )
    assert response.status_code == 422
    assert HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# Тест метода PUT при загрузке от 16 файлов
def test_put_main_manyph():
    full_test_path = os.path.join('files_for_tests', 'test_ph.jpg')
    image = [('image', open(full_test_path, 'rb')) for i in range(0, 20)]
    response = client.put(
        "/frame/",
        files=image,
        headers={'Authorization': f'Bearer {user_dict["username"]}'}
    )
    assert response.status_code == 413
    assert HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="too much images")


# Тест метода PUT при загрузке ошибочного файла (не правильного типа)
def test_put_main_1errph():
    full_test_path = os.path.join('files_for_tests', 'test_error_file.txt')
    image = [('image', open(full_test_path, 'rb'))]
    response = client.put(
        "/frame/",
        files=image,
        headers={'Authorization': f'Bearer {user_dict["username"]}'}
    )
    assert response.status_code == 415
    assert HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="media type not supported")


# Тест метода GET
def test_get_main():
    response = client.get("/frame/-1")
    assert response.status_code == 422


# Тест метода DELETE при удалении несуществующего кода запроса
def test_delete_main():

    response = client.delete("/frame/-1", headers={'Authorization': f'Bearer {user_dict["username"]}'})
    assert response.status_code == 422
    assert HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="resource not found")


# Тест метода DELETE при удалении существующего кода запроса
def test_delete_main5():
    response = client.delete("/frame/1", headers={'Authorization': f'Bearer {user_dict["username"]}'})
    assert response.status_code == 200
