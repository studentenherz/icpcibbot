import asyncio
import os

from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from telebot.util import update_types
from dotenv import load_dotenv

from db import DBHandler
from utils import is_admin_guard

load_dotenv()

bot = AsyncTeleBot(os.environ["TOKEN"], parse_mode="HTML")
db_handler = DBHandler("db.sqlite3")


@bot.message_handler(commands=["start"])
async def handle_start(message):
    await bot.reply_to(message, "Hello from icpcibbot!")


@bot.message_handler(commands=["tags"])
@is_admin_guard
async def handle_tags_list(message: Message):
    tags = db_handler.get_tags()
    resp_msg = "NO TAGS" if len(tags) == 0 else "\n".join(tags)

    await bot.send_message(message.chat.id, "<pre>{}</pre>".format(resp_msg))


@bot.message_handler(commands=["add"])
@is_admin_guard
async def handle_tags_add(message: Message):
    if message.text:
        tag = message.text.split(" ")[1]
        if db_handler.insert_tag(tag):
            await bot.reply_to(message, "Tag added successfully")
        else:
            await bot.reply_to(message, "There was a problem")


@bot.message_handler(commands=["del"])
@is_admin_guard
async def handle_tags_delete(message: Message):
    if message.text:
        tag = message.text.split(" ")[1]
        if db_handler.delete_tag(tag):
            await bot.reply_to(message, "Tag deleted successfully")
        else:
            await bot.reply_to(message, "There was a problem")


def create_keyboard(user_id: int | str, checked: str | None = None):
    tags = db_handler.get_tags()
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="{} {}".format("✅" if checked == tag else "", tag),
                    callback_data=f"{user_id}_{tag}",
                )
                for tag in tags
            ]
        ]
    )
    return keyboard


async def ask_university(chat_id: int | str, name: str, user_id: int | str):
    keyboard = create_keyboard(user_id)
    await bot.send_message(
        chat_id,
        f"Hola, {name}. Antes de continuar me podrías decir, ¿a qué universidad perteneces?",
        reply_markup=keyboard,
    )


@bot.message_handler(content_types=["new_chat_members"])
async def handle_member_new(message: Message):
    for user in message.new_chat_members or []:
        await ask_university(message.chat.id, user.first_name, user.id)


@bot.message_handler(
    func=lambda message: message.chat.type == "group"
    or message.chat.type == "supergroup"
)
async def handle_all_other_messages(message: Message):
    if message.from_user:
        user_id = message.from_user.id
        chat_id = message.chat.id

        chat_member = await bot.get_chat_member(chat_id, user_id)

        if not chat_member.custom_title:
            await ask_university(chat_id, message.from_user.first_name, user_id)


@bot.callback_query_handler(func=lambda q: True)
async def handler_callback_query(query: CallbackQuery):
    if query.data:
        user_id, tag = query.data.split("_")
        user_id = int(user_id)

        if user_id != query.from_user.id:
            await bot.answer_callback_query(
                query.id, "No te pregunté a ti", show_alert=True
            )
            return

        chat_id = query.message.chat.id

        await bot.edit_message_reply_markup(
            chat_id,
            query.message.id,
            reply_markup=create_keyboard(user_id, checked=tag),
        )

        if tag:
            await bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
            await bot.set_chat_administrator_custom_title(chat_id, user_id, tag)

    await bot.answer_callback_query(query.id, "Listo, ¡gracias!")


if __name__ == "__main__":
    asyncio.run(bot.polling(allowed_updates=update_types))
