import os
import discord
import requests
from nudeny import Classify, Detect
from io import BytesIO
from dotenv import load_dotenv
from utils import censor_image
load_dotenv()

TOKEN = os.environ.get('TOKEN')

classify = Classify()
detect = Detect()

client = discord.Client(intents=discord.Intents(
    message_content=True, messages=True, guild_messages=True))

guilds_settings = []

@client.event
async def on_ready():
    for guild in client.guilds:
        guilds_settings.append({
            "guild_id": guild.id,
            "kick_member": False,
            "ban_member": False,
            "spoiler": False,
            "classification": False,
            "censor": True
        })

    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    SUPPORTED_FILE_TYPE = ['.jpg','.jpeg','.png','.bmp', '.jfif']
    urls = []
    filenames = []
    safe_urls = []
    safe_filenames = []
    author = ""
    nude_counter = 0
    files = []
    unsupported_urls = []
    unsupported_filenames = []
    settings = {}

    if (message.author.bot == False):

        for guild in guilds_settings:
            if guild['guild_id'] == message.guild.id:
                settings = guild
                break

        if (len(message.attachments) > 0):
            author = message.author.name
            for attachment in message.attachments:
                extension = os.path.splitext(attachment.filename)[1]
                if extension in SUPPORTED_FILE_TYPE:
                    urls.append(attachment.url)
                    filenames.append(attachment.filename)
                else:
                    unsupported_urls.append(attachment.url)
                    unsupported_filenames.append(attachment.filename)
            await message.delete()

            if settings['classification']:
                response = classify.imageClassifyUrl(urls=urls)
                predictions = response['Prediction']
                for index, prediction in enumerate(predictions):
                    if prediction['class'] == "nude":
                        nude_counter += 1
                    else:
                        safe_urls.append(urls[index])
                        safe_filenames.append(filenames[index])
                
                for index, url in enumerate(safe_urls):
                    response = requests.get(url, stream=True)
                    data = BytesIO(response.content)
                    files.append(discord.File(data, filename=safe_filenames[index]))

                message_string = "Posted by: {}".format(author)
                if nude_counter > 0:
                    message_string = message_string + " {} image(s) contains nudity.".format(nude_counter)
                await message.channel.send(message_string, files = files)

            elif settings['censor']:
                response = detect.detectExposedFromUrl(urls=urls)
                predictions = response['Prediction']
                for index, prediction in enumerate(response['Prediction']):
                    data = censor_image(prediction)
                    files.append(discord.File(data, filename=filenames[index]))
                message_string = "Posted by: {}".format(author)
                await message.channel.send(message_string, files = files)
            
            for index, unsupported_url in enumerate(unsupported_urls):
                response = requests.get(unsupported_url)
                unsupported_files = discord.File(BytesIO(response.content), filename=unsupported_filenames[index])
                await message.channel.send(file=unsupported_files)


client.run(TOKEN)
