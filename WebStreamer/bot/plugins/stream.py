# This file is a part of TG-FileStreamBot
# Coding : Jyothis Jayanth [@EverythingSuckz]

import logging
from pyrogram import filters, errors
from WebStreamer.vars import Var
from urllib.parse import quote_plus
from WebStreamer.bot import StreamBot, logger
from WebStreamer.utils import get_hash, get_name
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from WebStreamer.bot.plugins.start import user_collection
from time import time


@StreamBot.on_message(
    filters.private
    & (
        filters.document
        | filters.video
        | filters.audio
        | filters.animation
        | filters.voice
        | filters.video_note
        | filters.photo
        | filters.sticker
    ),
    group=4,
)
async def media_receive_handler(_, m: Message):
    user_id = m.from_user.id
    
    # Check if the user is the admin and skip verification
    if user_id == Var.ADMIN_ID:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
        file_hash = get_hash(log_msg, Var.HASH_LENGTH)
        stream_link = f"{Var.URL}{log_msg.id}/{quote_plus(get_name(m))}?hash={file_hash}"
        
        try:
            await m.reply_text(
                text="<code>{}</code>".format(
                    stream_link),
                quote=True,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Open", url=stream_link)]]
                ),
            )
        except errors.ButtonUrlInvalid:
            await m.reply_text(
                text="<code>{}</code>".format(
                    stream_link),
                quote=True,
                parse_mode=ParseMode.HTML,
            )
    else:
        user_data = user_collection.find_one({'user_id': user_id, 'status': 'verified'})
        
        if user_data:
            current_time = time()
            token_expiration_time = user_data.get('time', 0) + Var.TOKEN_TIMEOUT
            if current_time > token_expiration_time:
                await m.reply("Your token🎟 has expired. Please tap here 👉 /start to renew your token🎟.")
            else:
                log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
                file_hash = get_hash(log_msg, Var.HASH_LENGTH)
                stream_link = f"{Var.URL}{log_msg.id}/{quote_plus(get_name(m))}?hash={file_hash}"
                
                try:
                    await m.reply_text(
                        text="<code>{}</code>".format(
                            stream_link),
                        quote=True,
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Open", url=stream_link)]]
                        ),
                    )
                except errors.ButtonUrlInvalid:
                    await m.reply_text(
                        text="<code>{}</code>".format(
                            stream_link),
                        quote=True,
                        parse_mode=ParseMode.HTML,
                    )
        else:
            await m.reply("You need to verify your token🎟 first. Please tap here 👉 /start to verify your token🎟.")







