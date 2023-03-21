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

def get_guild_settings(guilds_settings, id):
    for guild in guilds_settings:
        if guild['guild_id'] == id:
            return guild

def display_guild_settings(guild_settings):
    embed = discord.Embed(title="Nudeny Settings", description="`!nudeny <setting> <True/False>`", colour=discord.Colour.from_rgb(35, 224, 192))
    embed.add_field(name="**filter:** `{}`".format(guild_settings['filter']), value="(*Remove nude or sexy image*)", inline=False)
    embed.add_field(name="**censor:** `{}`".format(guild_settings['censor']), value="(*Censor exposed body parts. Not applicable to sexy images.*)", inline=False)
    embed.add_field(name="**spoiler:** `{}`".format(guild_settings['spoiler']), value="(*Instead of removing nude or sexy image spoiler is applied instead.*)", inline=False)
    embed.add_field(name="**include_sexy:** `{}`".format(guild_settings['include_sexy']), value="(*If set to True, sexy images will be included for Filter and Spoiler.*)", inline=False)
    embed.add_field(name="**kick_member:** `{}`".format(guild_settings['kick_member']), value="(*If set to True, the user that sends a nude image will be kicked.*)", inline=False)
    embed.add_field(name="**ban_member:** `{}`".format(guild_settings['ban_member']), value="(*If set to True, the user that sends a nude image will be banned.*)", inline=False)
    embed.set_footer(text="Please note that when the \"censor\" setting is turned on, the \"filter\" setting will automatically turn off, and vice versa. Additionally, the \"spoiler\" setting only works with the \"filter\" setting.")
    return embed