"""
import os
import math
import imghdr
from PIL import Image
from telegram import Bot as tg
from telegram import TelegramError
from AsunaBot.utils.botinfo import BOT_USERNAME
from AsunaBot import BOT_TOKEN
from AsunaBot import app
from pyrogram import filters
from AsunaBot.utils.errors import capture_err

__MODULE__ = "Stickers"
__HELP__ = "/sticker_id - To Get File ID of A Sticker.
/kang - To Kang A Sticker or Image."



@app.on_message(filters.command("sticker_id") & ~filters.edited)
@capture_err
async def sticker_id(_, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a sticker.")
        return
    if not message.reply_to_message.sticker:
        await message.reply_text("Reply to a sticker.")
        return
    file_id = message.reply_to_message.sticker.file_id
    await message.reply_text(f"`{file_id}`")


updater = tg(BOT_TOKEN)


@app.on_message(filters.command("kang") & ~filters.edited)
@capture_err
async def kang(client, message):
    args = message.text.split()
    msg = await message.reply_text("Kanging Sticker..")
    user = message.from_user
    packnum = 0
    packname = "f" + str(user.id) + "_by_"+ BOT_USERNAME
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = updater.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = "f" + str(packnum) + "_" + \
                    str(user.id) + "_by_"+BOT_USERNAME
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "images/kangsticker.png"
    if message.reply_to_message:
        if message.reply_to_message.sticker:
            file_id = message.reply_to_message.sticker.file_id
        elif message.reply_to_message.photo:
            file_id = message.reply_to_message.photo.file_id
        elif message.reply_to_message.document:
            file_id = message.reply_to_message.document.file_id
        else:
            await msg.edit("Nope.")
            return
        await msg.edit("Kanging.....")
        await app.download_media(file_id, file_name='images/kangsticker.png')
        image_type = imghdr.what(kangsticker)
        if image_type != 'jpeg' and image_type != 'png' and image_type != 'webp':
            await msg.edit("Format not supported! ({})".format(image_type))
            return
        if len(args) > 1:
            sticker_emoji = str(args[1])
        elif message.reply_to_message.sticker and message.reply_to_message.sticker.emoji:
            sticker_emoji = message.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"
        try:
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            if not message.reply_to_message.sticker:
                im.save(kangsticker, "PNG")
            updater.add_sticker_to_set(user_id=user.id, name=packname,
                                       png_sticker=open('images/kangsticker.png', 'rb'), emojis=sticker_emoji)
            await msg.edit("Sticker Kanged [pack](t.me/addstickers/{})\nEmoji: ```{}```".format(packname, sticker_emoji))
        except OSError as e:
            await message.reply_text("Something wrong happened.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                await msg.edit("Kanging")
                await makepack_internal(msg, user, open('images/kangsticker.png', 'rb'), sticker_emoji, updater, packname, packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                updater.add_sticker_to_set(user_id=user.id, name=packname,
                                           png_sticker=open('images/kangsticker.png', 'rb'), emojis=sticker_emoji)
                await msg.edit("Sticker Kanged [pack](t.me/addstickers/{})\nEmoji: ```{}```".format(packname, sticker_emoji))
            elif e.message == "Invalid sticker emojis":
                await msg.edit("Invalid emoji")
            elif e.message == "Stickers_too_much":
                await msg.edit("Too much stickers")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                await msg.edit("Sticker Kanged [pack](t.me/addstickers/{})\nEmoji: ```{}```".format(packname, sticker_emoji))
            print(e)
    else:
        packs = "Please reply to a sticker\nhere is your pack:\n"
        if packnum > 0:
            firstpackname = "c" + str(user.id) + "_by_"+ BOT_USERNAME
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[pack{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[pack](t.me/addstickers/{packname})"
            await msg.edit(packs)
    if os.path.isfile("images/kangsticker.png"):
        os.remove("images/kangsticker.png")


async def makepack_internal(msg, user, png_sticker, emoji, updater, packname, packnum):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        success = updater.create_new_sticker_set(user.id, packname, f"{name}'s AsunaBot pack" + extra_version,
                                                 png_sticker=png_sticker,
                                                 emojis=emoji)
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            await msg.edit("Your pack can be found [here](t.me/addstickers/%s)" % packname)
        elif e.message == "Peer_id_invalid":
            await msg.edit("Contact me in PM first.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                text="Start", url=f"t.me/{bot_username}")]]))
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            await msg.edit("Sticker pack successfully created. Get it [here](t.me/addstickers/%s)" % packname)
        return

    if success:
        await msg.edit("Sticker pack successfully created. Get it [here](t.me/addstickers/%s)" % packname)
    else:
        await msg.edit("Failed to create sticker pack.")"""
