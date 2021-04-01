import re
import time
from pyrogram import filters, types
import speedtest
import psutil
from AsunaBot import app, SUDOERS, bot_start_time
from AsunaBot.utils import nekobin, formatter
from AsunaBot.utils.errors import capture_err
from AsunaBot.utils.botinfo import BOT_ID
from AsunaBot.utils.dbfunctions import (
    is_gbanned_user,
    add_gban_user,
    remove_gban_user,
    get_served_chats
)


__MODULE__ = "Sudoers"
__HELP__ = '''/log - To Get Logs From Last Run.
/speedtest - To Perform A Speedtest.
/stats - To Check System Status.
/global_stats - To Check Bot's Global Stats.
/gban - To Ban A User Globally.
/broadcast - To Broadcast A Message In All Groups.'''


# Logs Module


@app.on_message(filters.user(SUDOERS) & filters.command("log"))
@capture_err
async def logs_chat(_, message):
    keyb = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(
                    "Paste on Nekobin", callback_data="paste_log_nekobin"
                )
            ]
        ]
    )
    await message.reply_document(
        "error.log", reply_markup=keyb
    )


def logs_callback(_, __, query):
    if re.match("paste_log_nekobin", query.data):
        return True


logs_create = filters.create(logs_callback)


@app.on_callback_query(logs_create)
async def paste_log_neko(client, query):
    if query.from_user.id in SUDOERS:
        j = open("error.log", "r")
        data = await nekobin.neko(j.read())
        keyb = types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton("Pasted!", url=f"{data}")]]
        )
        await query.message.edit_caption("Successfully Nekofied",
                                         reply_markup=keyb)
    else:
        await client.answer_callback_query(
            query.id, "'Blue Button Must Press', huh?", show_alert=True
        )


# SpeedTest Module


def speed_convert(size):
    power = 2 ** 10
    zero = 0
    units = {0: "", 1: "Kb/s", 2: "Mb/s", 3: "Gb/s", 4: "Tb/s"}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"


@app.on_message(
    filters.user(SUDOERS) & filters.command("speedtest")
)
@capture_err
async def get_speedtest_result(_, message):
    m = await message.reply_text("`Performing A Speedtest!`")
    speed = speedtest.Speedtest()
    i = speed.get_best_server()
    j = speed.download()
    k = speed.upload()
    await m.edit(f'''
**Download:** {speed_convert(j)}
**Upload:** {speed_convert(k)}
**Latency:** {round((i["latency"]))} ms
```''')

# Stats Module


async def bot_sys_stats():
    bot_uptime = int(time.time() - bot_start_time)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = f'''
Uptime: {formatter.get_readable_time((bot_uptime))}
CPU: {cpu}%
RAM: {mem}%
Disk: {disk}%'''
    return stats


@app.on_message(
    filters.user(SUDOERS) & filters.command("stats")
)
@capture_err
async def get_stats(_, message):
    stats = await bot_sys_stats()
    await message.reply_text(stats)

# Gban


@app.on_message(filters.command("gban") & filters.user(SUDOERS))
@capture_err
async def ban_globally(_, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a user's message to Gban.")
        return
    from_user_id = message.from_user.id
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    from_user_mention = message.from_user.mention
    if user_id == from_user_id:
        await message.reply_text("You want to gban yourself? FOOL!")
    elif user_id == BOT_ID:
        await message.reply_text("Should i gban myself? I'm not fool like you, HUMAN!")
    elif user_id in SUDOERS:
        await message.reply_text("You want to ban a sudo user? GET REKT!!")
    else:
        is_gbanned = await is_gbanned_user(user_id)
        if is_gbanned:
            await message.reply_text("He's already gbanned, why bully him?")
        else:
            served_chats = await get_served_chats()
            for served_chat in served_chats:
                try:
                    await app.kick_chat_member(served_chat['chat_id'], user_id)
                except Exception:
                    pass
            await add_gban_user(user_id)
            try:
                await app.send_message(
                    user_id, f"""
Hello, You have been globally banned by {from_user_mention},
You can appeal for this ban by talking to {from_user_mention} about this.""")
            except Exception:
                pass
            await message.reply_text(f"Banned {mention} Globally!")

# Ungban


@app.on_message(filters.command("ungban") & filters.user(SUDOERS))
@capture_err
async def unban_globally(_, message):
    if not message.reply_to_message:
        await message.reply_to_message("Reply to a user's message to ungban.")
        return
    from_user_id = message.from_user.id
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    if user_id == from_user_id:
        await message.reply_text("You want to ungban yourself? FOOL!")
    elif user_id == BOT_ID:
        await message.reply_text("Should i ungban myself? But i'm not gbanned.")
    elif user_id in SUDOERS:
        await message.reply_text("Sudo users can't be gbanned/ungbanned.")
    else:
        is_gbanned = await is_gbanned_user(user_id)
        if not is_gbanned:
            await message.reply_text("He's already free, why bully him?")
        else:
            await remove_gban_user(user_id)
            await message.reply_text(f"Unbanned {mention} Globally!")

# Broadcast


@app.on_message(
    filters.command("broadcast")
    & filters.user(SUDOERS)
    & ~filters.edited
)
@capture_err
async def broadcast_message(_, message):
    if len(message.command) < 2:
        await message.reply_text("**Usage**:\n/broadcast [MESSAGE]")
        return
    text = message.text.split(None, 1)[1]
    sent = 0
    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))
    for i in chats:
        try:
            await app.send_message(i, text=text)
            sent += 1
        except Exception:
            pass
    await message.reply_text(f"**Broadcasted Message In {sent} Chats.**")
