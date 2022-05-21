import hashlib
from fastapi import status, HTTPException, Depends
from schemas import *

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


def save_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)


def hash_password(password: str):
    """Пароль хэшируется с помощью метода md5"""
    return hashlib.md5(password.encode()).hexdigest()


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
