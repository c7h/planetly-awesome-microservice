import os
import motor.motor_asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import MongoDBUserDatabase


mongo_host = os.getenv('MONGO_HOST')
mongo_port = os.getenv('MONGO_PORT')

SECRET = os.getenv('SECRET')
DATABASE_URL = f"mongodb://{mongo_host}:{mongo_port}"

# CORS Origins.
origins = [
    "http://api.planetly.com",
    "https://planetly.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8000",
]


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, uuidRepresentation="standard"
)
db = client["database_name"]
collection = db["users"]
user_db = MongoDBUserDatabase(UserDB, collection)


def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(user: UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")


def after_verification_request(user: UserDB, token: str, request: Request):
    print(f"Verification requested for user {user.id}. Verification token: {token}")


jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds=3600, tokenUrl="auth/jwt/login"
)


app = FastAPI(title="Planetly User Service")


# For usage as a nice little microservice, we would like to
# access authentication from other services too. This is why we need to
# set CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)
app.include_router(
    fastapi_users.get_auth_router(jwt_authentication), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(on_after_register), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(
        SECRET, after_forgot_password=on_after_forgot_password
    ),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(
        SECRET, after_verification_request=after_verification_request
    ),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])
