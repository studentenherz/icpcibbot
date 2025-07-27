import os
import functools

from telebot.types import Message
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = int(os.environ["ADMIN_ID"])


def is_admin_guard(func):
    @functools.wraps(func)
    async def wrapper(message: Message):
        if message.from_user and message.from_user.id == ADMIN_ID:
            await func(message)

    return wrapper
