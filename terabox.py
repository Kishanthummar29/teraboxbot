import subprocess
import sys

# Function to install required packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required packages
required_packages = ["telebot", "requests", "m3u8"]

# Install missing packages
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

import telebot
import requests
import m3u8
import os
from concurrent.futures import ThreadPoolExecutor

# Replace with your Telegram bot token
token = '6496212304:AAE9BrtjXFMy_N0gRWRiuUckS7rkBM4sTis'
bot = telebot.TeleBot(token)

# Extract video ID from any Terabox URL
def extract_video_id(url):
    import re
    match = re.search(r'/s/1([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    username = message.from_user.username or message.from_user.first_name
    bot.reply_to(message, f"WELCOME TO TERABOX VIDEO DOWNLOADER BOT😍\n\n❤️‍🔥 Username :- {username}\n\n🔥 ADMIN  :- \n")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text

    # Ignore the /start command
    if text == '/start':
        return

    video_id = extract_video_id(text)
    print(f"Extracted video ID: {video_id}")  # Debugging line

    if not video_id:
        bot.reply_to(message, 'Please send a valid Terabox Video Link.')
        return

    bot.send_chat_action(message.chat.id, 'typing')

    api_url = f'https://example.com/{video_id}'
    print(f"API URL: {api_url}")  # Debugging line

    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        print(f"API Response: {data}")  # Debugging line

        if data.get('status') == 'success':
            m3u8_link = data.get('source')
            bot.send_chat_action(message.chat.id, 'typing')
            video_path = download_video(m3u8_link, video_id)
            if video_path:
                bot.send_chat_action(message.chat.id, 'upload_video')
                with open(video_path, 'rb') as video_file:
                    bot.send_video(message.chat.id, video_file, caption=f'AX Terabox Downloader (Video ID :- 1{video_id})')
                os.remove(video_path)
            else:
                bot.reply_to(message, 'Failed to download the video. Please try again later.')
        else:
            bot.reply_to(message, 'Failed to retrieve the video. Please try again later.')
    else:
        print(f"Error fetching video: {response.text}")
        bot.reply_to(message, 'An error occurred while processing your request. Please try again later.')

def download_segment(url, idx):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        segment_path = f'segment_{idx}.ts'
        with open(segment_path, 'wb') as segment_file:
            segment_file.write(response.content)
        return segment_path
    else:
        print(f"Failed to download segment: {url}")
        return None

def download_video(m3u8_url, video_id):
    try:
        m3u8_obj = m3u8.load(m3u8_url)
        ts_urls = [segment.uri for segment in m3u8_obj.segments]

        video_path = f'{video_id}.ts'
        segment_paths = []

        with ThreadPoolExecutor(max_workers=20) as executor:  # Increased number of threads
            futures = [executor.submit(download_segment, url, idx) for idx, url in enumerate(ts_urls)]
            for future in futures:
                segment_path = future.result()
                if segment_path:
                    segment_paths.append(segment_path)
                else:
                    return None

        # Concatenate all segments into one video file
        with open(video_path, 'wb') as video_file:
            for segment_path in segment_paths:
                with open(segment_path, 'rb') as segment_file:
                    video_file.write(segment_file.read())
                os.remove(segment_path)
        return video_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

if __name__ == '__main__':
    bot.polling()
