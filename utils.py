import os
import cv2
import discord
import numpy as np
import requests
from io import BytesIO

def censor_image(prediction):
    response = requests.get(prediction['source'])
    image_data = response.content
    image_array = np.asarray(bytearray(image_data), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    for part in prediction['exposed_parts']:
        for detection in prediction['exposed_parts'][part]:
            start_point = (detection['left'] - 20, detection['top'] - 20)
            end_point = (detection['right'] + 20, detection['bottom'] + 20)
            cv2.rectangle(image, start_point, end_point, (0, 0, 0), -1)

    _, image_data = cv2.imencode(".jpg", image)
    image_bytes = BytesIO(image_data.tobytes())

    return image_bytes

def get_image_attachments(attachments):
    SUPPORTED_FILE_TYPE = ['.jpg','.jpeg','.png','.bmp', '.jfif']
    image_urls = []
    image_filenames = []
    unsupported_file_urls = []
    unsupported_file_filenames = []

    for attachment in attachments:
        extension = os.path.splitext(attachment.filename)[1]
        if extension in SUPPORTED_FILE_TYPE:
            image_urls.append(attachment.url)
            image_filenames.append(attachment.filename)
        else:
            unsupported_file_urls.append(attachment.url)
            unsupported_file_filenames.append(attachment.filename)

    return image_urls, image_filenames, unsupported_file_urls, unsupported_file_filenames

def is_valid_setting(setting):
    SETTINGS = ['kick_member', 'ban_member', 'spoiler', 'filter', 'include_sexy', 'censor']
    setting = setting.lower()

    if setting in SETTINGS:
        return True
    
    return False

def display_guild_settings(guild_settings):
    embed = discord.Embed(title="Nudeny Settings", color=discord.Color.green)
    embed.add_field(name="**Filter:** *remove nude or sexy image*", value="`{}`".format(guild_settings['filter']), inline=False)
    return embed