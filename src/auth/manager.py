from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from database import User, get_user_db
from funcs import headers

SECRET = "SECRET"


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response=None
    ):
        headers['Client-Id'] = str(user.client_id)
        headers['Api-Key'] = user.api_key


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
