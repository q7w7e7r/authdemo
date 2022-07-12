# FastAPI Server 
import hmac
import hashlib
import base64
import json
from typing import Optional
from fastapi import FastAPI, Form, Cookie
from fastapi.responses import Response

app = FastAPI()

SECRET_KEY = "11f07600cf9ac682cabfe4c58d82d6149a501b473b6cab0ec5802b30fef801b9"
PASSWORD_SALT = "6d3a27890562915fa660ac3fbfbdbb57bd715e82040bc8f20319de57a2c35698"


def sign_data(data: str) -> str:
    """Возвращает подписанные данные data"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256(
        (password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = {
    "Vasiliy@gmail.com": {
        "name": "Василий",
        "password": "5918908ce23a542208cf48a4eb6f1c3efa8c78a8e665ba38629ec143c4f6e466",  # 12345
        "balance": 100_000
    },
    "petr@gmail.com": {
        "name": "Пётр",
        "password": "82b5cf273698ea86dcd3bed8b575b4bac1cb56fb73447c19ca6ef2fd562af307",  # 67890
        "balance": 250_000
    }
}


@app.get("/")
def index_page(username: Optional[str] = Cookie(default=None)):
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type='text/html')
    valid_username = get_username_from_signed_string(username_signed=username)
    if not valid_username:
        response = Response(login_page, media_type='text/html')
        response.delete_cookie(key="username")
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type='text/html')
        response.delete_cookie(key="username")
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}!<br/>"
        f"Баланс: {users[valid_username]['balance']}!<br/>"
        , media_type='text/html')


@app.post("/login")
def process_login_page(username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "я вас не знаю!"
            }),
            media_type="application/json")
    response = Response(
        json.dumps({
            "success": True,
            "message": f"Привет, {user['name']}!<br/> Баланс {user['balance']}"
        }),
        media_type='application/json')
    username_signed = base64.b64encode(
        username.encode()).decode() + "." + sign_data(username)
    response.set_cookie(key="username", value=username_signed)
    return response
