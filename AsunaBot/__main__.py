import asyncio
import re
import importlib
import time
import uvloop
from pyrogram import filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from AsunaBot import app, MOD_NOLOAD
from AsunaBot.utils import get_info, paginate_modules
from AsunaBot.utils import botinfo, formatter
from AsunaBot.modules.sudoers import bot_sys_stats
from AsunaBot.modules import ALL_MODULES
from AsunaBot import bot_start_time

loop = asyncio.get_event_loop()


HELPABLE = {}


async def start_bot():
    await app.start()
    await get_info(app)

    for module in ALL_MODULES:
        imported_module = importlib.import_module("AsunaBot.modules." + module)
        if (
            hasattr(imported_module, "__MODULE__")
            and imported_module.__MODULE__
        ):
            if imported_module.__MODULE__.lower() in MOD_NOLOAD:
                continue
            imported_module.__MODULE__ = imported_module.__MODULE__
            if (
                hasattr(imported_module, "__HELP__")
                and imported_module.__HELP__
            ):
                HELPABLE[
                    imported_module.__MODULE__.lower()
                ] = imported_module

    bot_modules = ""
    j = 1
    for i in ALL_MODULES:
        if j == 4:
            bot_modules += "|{:<15}|\n".format(i)
            j = 0
        else:
            bot_modules += "|{:<15}".format(i)
        j += 1
    print("+===============================================================+")
    print("|                    AsunaBot - Modules                         |")
    print("+===============+===============+===============+===============+")
    print(bot_modules)
    print("+===============+===============+===============+===============+")
    print("Bot Started Successfully as {}!".format(botinfo.BOT_NAME))
    print("Repository : https://github.com/Zer0-Tw0/AsunaBot")
    await idle()


@app.on_message(filters.command("start"))
async def start(_, message):
    bot_uptime = int(time.time() - bot_start_time)
    await message.reply_text(
        "Hi there! \nI am an Anime themed group management bot.\n"
        f"Already Online Since {formatter.get_readable_time((bot_uptime))},\n"
        "You can find my list of available commands with /help.\n"
        )

@app.on_message(filters.command("help"))
async def help_command(_, message):
    if message.chat.type != "private":
        if len(message.command) >= 2 and message.command[1] == "help":
            text, keyboard = await help_parser(message)
            await message.reply(
                text, reply_markup=keyboard, disable_web_page_preview=True
            )
            return
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Help",
                        url=f"t.me/{botinfo.BOT_USERNAME}?start=help",
                    ),
                    InlineKeyboardButton(
                        text="Repo",
                        url="https://github.com/Zer0-Tw0/AsunaBot",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="System Stats",
                        callback_data="stats_callback"
                    ),
                    InlineKeyboardButton(
                        text="Support",
                        url="t.me/StrawHatGroup"
                    )
                ]
            ]
        )
        await message.reply("Pm Me For More Details.", reply_markup=keyboard)
        return
    keyboard = InlineKeyboardMarkup(
        [    
            [
                InlineKeyboardButton(
                    text="Module",
                    callback_data="bot_commands"
                ),
                InlineKeyboardButton(
                    text="Repo",
                    url="https://github.com/Zer0-Tw0/AsunaBot"
                )
            ],
            [
                InlineKeyboardButton(   
                    text="System Stats",
                    callback_data="stats_callback"
                ),
                InlineKeyboardButton(
                    text="Support",
                    url="t.me/StrawHatGroup"
                )
            ]
        ]
    )
    await message.reply("Hello, Choose An Option From Below.", reply_markup=keyboard)





async def help_parser(name, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    return (
        "Yo! {first_name}, I am {bot_name}, Here is the list of all possible module:".format(
            first_name=name,
            bot_name=botinfo.BOT_NAME,
        ),
        keyboard,
    )


@app.on_callback_query(filters.regex("bot_commands"))
async def end_callbacc(_, CallbackQuery):
    text, keyboard = await help_parser(CallbackQuery.from_user.mention)
    await app.send_message(
            CallbackQuery.message.chat.id,
            text=text,
            reply_markup=keyboard
            )

    await CallbackQuery.message.delete()

@app.on_callback_query(filters.regex("stats_callback"))
async def end_callbacc(_, CallbackQuery):
    text = await bot_sys_stats()
    await app.answer_callback_query(CallbackQuery.id, text, show_alert=True)


@app.on_callback_query(filters.regex(r"help_(.*?)"))
async def help_button(client, query):
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    create_match = re.match(r"help_create", query.data)

    if mod_match:
        module = mod_match.group(1)
        text = (
            "{} **{}**:\n".format(
                "Here is the help for", HELPABLE[module].__MODULE__
            )
            + HELPABLE[module].__HELP__
        )

        await query.message.edit(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("back", callback_data="help_back")]]
            ),
            disable_web_page_preview=True,
        )

    elif prev_match:
        curr_page = int(prev_match.group(1))
        await query.message.edit(
            text="Hi {first_name}. I am {bot_name}".format(
                first_name=query.from_user.first_name,
                bot_name=botinfo.BOT_NAME,
            ),
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(curr_page - 1, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif next_match:
        next_page = int(next_match.group(1))
        await query.message.edit(
            text="Hi {first_name}. I am {bot_name}".format(
                first_name=query.from_user.first_name,
                bot_name=botinfo.BOT_NAME,
            ),
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(next_page + 1, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif back_match:
        await query.message.edit(
            text="Hi {first_name}. I am {bot_name}".format(
                first_name=query.from_user.first_name,
                bot_name=botinfo.BOT_NAME,
            ),
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, HELPABLE, "help")
            ),
            disable_web_page_preview=True,
        )

    elif create_match:
        text, keyboard = await help_parser(query)
        await query.message.edit(
            text=text, reply_markup=keyboard, disable_web_page_preview=True
        )

    return await client.answer_callback_query(query.id)


if __name__ == "__main__":
    uvloop.install()
    loop.run_until_complete(start_bot())
