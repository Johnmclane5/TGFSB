# This file is a part of TG-FileStreamBot
# Coding : Jyothis Jayanth [@EverythingSuckz]
import os
import logging
import asyncio
import uuid
import pyshorteners
import requests
from time import sleep, time
from base64 import b64encode
from pyrogram import filters
from pymongo import MongoClient
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User

from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot

# MongoDB credentials
mongo_db_name = "file_stream"

# Initialize the MongoDB client and collection
mongo_client = MongoClient(Var.MONGODB_URI)
db = mongo_client[mongo_db_name]
user_collection = db['users']  # Collection to store user tokens

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output logs to the console
    ]
)

# Create a logger for the bot
logger = logging.getLogger(__name__)


@StreamBot.on_message(filters.command("start") & filters.private)
async def handle_start_command(_, m: Message):
    user_link = get_user_link(m.from_user) 
    try:
        user_id = m.from_user.id

        if Var.ALLOWED_USERS and not ((str(user_id) in Var.ALLOWED_USERS) or (m.from_user.username in Var.ALLOWED_USERS)):
            return await m.reply(
                "You are not in the allowed list of users who can use me. \
                Check <a href='https://github.com/EverythingSuckz/TG-FileStreamBot#optional-vars'>this link</a> for more info.",
                disable_web_page_preview=True, quote=True
            )

        # Get the token from the URL if it's present
        if len(m.command) > 1:
            provided_token = m.command[1]

            if verify_token(user_id, provided_token):
                # The user is verified successfully
                await m.reply("You token verified successfully!✅ Now you can send the file📂.")
                await StreamBot.send_message(
                    Var.LOG_CHANNEL_ID, f"User🕵️‍♂️ {user_link} with 🆔 {user_id} verified file stream🎟")
            else:
                # The provided token doesn't match the stored token
                await m.reply("Token Verification failed❌. Please click on the correct link to verify your token🎟.")
                await StreamBot.send_message(
                    Var.LOG_CHANNEL_ID, f"User🕵️‍♂️ {user_link} with 🆔 {user_id} tried the wrong link file stream")
        else:
            # Generate or update the user's token and send the verification link
            token = generate_or_update_token(user_id)
            bot_info = await StreamBot.get_me()
            bot_username = bot_info.username
            url_to_shorten = f'https://telegram.me/{bot_username}?start={token}'
            shortened_url = tiny(shorten_url(url_to_shorten))

            # Create an inline keyboard with the button for the shortened URL
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Verify your token", url=shortened_url)]])

            # Send the message with the verification button
            sent_message = await m.reply("Welcome! To 🗄HR File-Stream, Please verify✅ your token🎟:", reply_markup=keyboard)
            await StreamBot.send_message(Var.LOG_CHANNEL_ID, f"User🕵️‍♂️ {user_link} with 🆔 {user_id} Joined File Stream")

            # Delete the sent message after 60 seconds
            await asyncio.sleep(60)  # Await the asynchronous sleep function
            await sent_message.delete()  # Await the delete method to delete the message

    except Exception as e:
        logger.error(f"Error while processing the start command: {e}")


def shorten_url(url):
    try:
        api_url = f"https://modijiurl.com/api"
        params = {
            "api": Var.URL_SHORTENER_API_KEY,
            "url": url,
            "format": "text"
        }
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.text.strip()
        else:
            logger.error(
                f"URL shortening failed. Status code: {response.status_code}, Response: {response.text}")
            return url
    except Exception as e:
        logger.error(f"URL shortening failed: {e}")
        return url

def tiny(long_url):
    s = pyshorteners.Shortener()
    try:
        short_url = s.clckru.short(long_url)
        logger.info(f'tinyfied {long_url} to {short_url}')
        return short_url
    except Exception:
        logger.error(f'Failed to shorten URL: {long_url}')
        return long_url
    
# Generate a random token and save it to the database for a new user or update existing user's token


def generate_or_update_token(user_id):
    user_data = user_collection.find_one({'user_id': user_id})
    current_time = time()

    if user_data:
        # The user already exists, check if the token is expired
        token_expiration_time = user_data.get('time', 0) + Var.TOKEN_TIMEOUT
        if current_time > token_expiration_time:
            # The token is expired, generate a new random token
            token = str(uuid.uuid4())  # Generate a new random token using uuid
            user_collection.update_one(
                {'user_id': user_id},
                {'$set': {'token': token, 'status': 'not verified', 'time': current_time}}
            )
        else:
            # The token is not expired, return the existing token
            token = user_data['token']
    else:
        # The user is new, generate a random token and add them to the database
        token = str(uuid.uuid4())  # Generate a random token using uuid
        user_collection.insert_one({
            'user_id': user_id,
            'token': token,
            'status': 'not verified',
            'time': current_time  # Save the current timestamp for token refresh
        })
    return token

# Verify the user's token and update status


def verify_token(user_id, provided_token):
    user_data = user_collection.find_one(
        {'user_id': user_id, 'token': provided_token})
    if user_data:
        # Update the user's status to 'verified'
        user_collection.update_one({'user_id': user_id}, {
                                   '$set': {'status': 'verified'}})
    return user_data is not None


def delete_message(chat_id, message):
    sleep(60)  # Wait for 60 seconds
    message.delete()  # Use the delete method to delete the message


@StreamBot.on_message(filters.command("token_time") & filters.private)
async def handle_token_time_command(_, m: Message):
    try:
        user_id = m.from_user.id

        # Check if the user's token is present in the database
        user_data = user_collection.find_one({'user_id': user_id})
        if user_data and 'time' in user_data:
            current_time = time()
            token_expiration_time = user_data['time'] + Var.TOKEN_TIMEOUT
            time_remaining = token_expiration_time - current_time

            if time_remaining <= 0:
                await StreamBot.send_message(
                    user_id, "Your token🎟 has expired. Please tap here 👉 /start to renew your token🎟.")
            else:
                minutes_remaining = float(time_remaining / 3600)
                sent_message = await StreamBot.send_message(
                    user_id, f"Your token will expire in {minutes_remaining:.1f} ⌚️hours.")

                # Delete the sent message after 60 seconds
                await asyncio.sleep(60)
                await sent_message.delete()
        else:
            await StreamBot.send_message(
                user_id, "You token🎟 not verified. Please tap here 👉 /start to verify your token🎟.")

    except Exception as e:
        logger.error(
            f"Error while processing the token_time_remaining command: {e}")

def get_user_link(user: User) -> str:
    user_id = user.id
    first_name = user.first_name
    return f'[{first_name}](tg://user?id={user_id})'
