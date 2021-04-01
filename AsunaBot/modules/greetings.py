import asyncio
from datetime import datetime
from pyrogram import filters
from AsunaBot import app, WELCOME_DELAY_KICK_SEC
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions, User
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, ChatAdminRequired
from AsunaBot.utils.errors import capture_err
from AsunaBot.utils.dbfunctions import is_gbanned_user


@app.on_message(filters.new_chat_members)
@capture_err
async def welcome(_, message: Message):
    """Mute new member and send message with button"""
    for member in message.new_chat_members:
        try:
            if member.is_bot:
                continue  # ignore bots
            if await is_gbanned_user(member.id):
                await message.chat.kick_member(member.id)
                continue
            text = (f"Welcome, {(member.mention())}\n**Are you human?**\n"
                    "You will be removed from this chat if you are not verified "
                    f"in {WELCOME_DELAY_KICK_SEC} seconds")
            await message.chat.restrict_member(member.id, ChatPermissions())
        except ChatAdminRequired:
            continue
        button_message = await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Press Here to Verify",
                            callback_data="pressed_button {}".format(member.id)
                        )
                    ]
                ]
            ),
            quote=True
        )
        asyncio.create_task(kick_restricted_after_delay(
            WELCOME_DELAY_KICK_SEC, button_message, member))
        await asyncio.sleep(0.5)


@app.on_callback_query(filters.regex("pressed_button"))
async def callback_query_welcome_button(client, callback_query):
    """After the new member presses the button, set his permissions to
    chat permissions, delete button message and join message
    """
    button_message = callback_query.message
    pending_user = await app.get_users(int(callback_query.data.replace('pressed_button ', '')))
    pressed_user_id = callback_query.from_user.id
    pending_user_id = pending_user.id
    if pending_user_id == pressed_user_id:
        await callback_query.answer("Captcha passed!, Have a nice stay.")
        await button_message.chat.unban_member(pending_user_id)
        await button_message.delete()
    else:
        await callback_query.answer("This is not for you")


async def kick_restricted_after_delay(delay, button_message: Message, user: User):
    """If the new member is still restricted after the delay, delete
    button message and join message and then kick him
    """
    await asyncio.sleep(delay)
    join_message = button_message.reply_to_message
    group_chat = button_message.chat
    user_id = user.id
    await join_message.delete()
    await button_message.delete()
    await _ban_restricted_user_until_date(group_chat, user_id, duration=delay)


@app.on_message(filters.left_chat_member)
@capture_err
async def left_chat_member(_, message: Message):
    """When a restricted member left the chat, ban him for a while"""
    group_chat = message.chat
    user_id = message.left_chat_member.id
    await _ban_restricted_user_until_date(group_chat, user_id,
                                          duration=WELCOME_DELAY_KICK_SEC)


async def _ban_restricted_user_until_date(group_chat,
                                          user_id: int,
                                          duration: int):
    try:
        member = await group_chat.get_member(user_id)
        if member.status == "restricted":
            until_date = int(datetime.utcnow().timestamp() + duration)
            await group_chat.kick_member(user_id, until_date=until_date)
    except UserNotParticipant:
        pass
