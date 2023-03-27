import os
import ast
import discord
from discord.ext import commands
from typing import Literal
import requests
from nudeny import Classify, Detect
from io import BytesIO
from dotenv import load_dotenv
from utils import censor_image, get_image_attachments, is_valid_setting, display_guild_settings, get_guild_settings, is_bool, set_guild_settings
load_dotenv()

TOKEN = os.environ.get('TOKEN')

classify = Classify()
detect = Detect()

# bot = discord.bot(intents=discord.Intents(
#     message_content=True, messages=True, guild_messages=True))

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents(
    message_content=True, messages=True, guild_messages=True, guilds=True))

guilds_settings = []

@bot.event
async def on_ready():
    for guild in bot.guilds:
        guilds_settings.append({
            "guild_id": guild.id,
            "kick_member": False,
            "ban_member": False,
            "spoiler": False,
            "filter": True,
            "include_sexy": False,
            "censor": False
        })
    synced = await bot.tree.sync()
    print("Synced {} command(s)".format(len(synced)))
    print(f'{bot.user} has connected to Discord!')

@bot.tree.command(name="set", description="Update Nudeny bot server settings.")
async def set(interaction: discord.Interaction, option: Literal['filter', 'censor', 'spoiler', 'include_sexy', 'kick_member', 'ban_member'],  value:Literal['True','False']):

    if interaction.user.guild_permissions.administrator == False:
        return await interaction.response.send_message("You don't have permission to use that command.")

    # Forces an error if option is empty
    type(option)
    
    if is_valid_setting(option) and value != None:
        try:
            if(is_bool(value)):
                value = value.title()
                value = ast.literal_eval(value)
                settings = get_guild_settings(guilds_settings, interaction.guild.id)
                settings = set_guild_settings(settings, option=option, value=value)
                await interaction.response.send_message(embed=display_guild_settings(guild_settings=settings))        
            else:
                await interaction.response.send_message("Invalid value. Please enter 'True' or 'False'.")
        except ValueError:
            await interaction.response.send_message("Invalid setting value. Please enter 'True' or 'False'.")
            return
    else:
        await interaction.response.send_message("Invalid option or value.")


@bot.tree.command(name="guide", description="Display Nudeny bot server settings.")
async def guide(interaction: discord.Interaction):
    settings = get_guild_settings(guilds_settings, interaction.guild_id)
    await interaction.response.send_message(embed=display_guild_settings(guild_settings=settings))

# @bot.command()
# @commands.has_permissions(administrator=True)
# async def set(ctx, option, *, value=None):

#     # Forces an error if option is empty
#     type(option)
    
#     if is_valid_setting(option) and value != None:
#         try:
#             if(is_bool(value)):
#                 value = value.title()
#                 value = ast.literal_eval(value)
#                 settings = get_guild_settings(guilds_settings, ctx.guild.id)
#                 settings = set_guild_settings(settings, option=option, value=value)
#                 await ctx.send(embed=display_guild_settings(guild_settings=settings))        
#             else:
#                 await ctx.send("Invalid value. Please enter 'True' or 'False'.")
#         except ValueError:
#             await ctx.send("Invalid setting value. Please enter 'True' or 'False'.")
#             return
#     else:
#         await ctx.send("Invalid option or value.")

# @bot.command()
# async def guide(ctx):
#     settings = get_guild_settings(guilds_settings, ctx.guild.id)
#     await ctx.send(embed=display_guild_settings(guild_settings=settings))  

# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.MissingPermissions):
#         await ctx.send("You don't have permission to use that command.")
#     else:
#         await ctx.send(error)

@bot.event
async def on_message(message):
    # SUPPORTED_FILE_TYPE = ['.jpg','.jpeg','.png','.bmp', '.jfif']
    image_urls = []
    image_filenames = []
    safe_urls = []
    safe_filenames = []
    author = ""
    nude_counter = 0
    files = []
    unsupported_file_urls = []
    unsupported_file_filenames = []
    settings = {}

    if (message.author.bot == False):

        for guild in guilds_settings:
            if guild['guild_id'] == message.guild.id:
                settings = guild
                break
            
        if (len(message.attachments) > 0):
            author = message.author.name
            image_urls, image_filenames, unsupported_file_urls, unsupported_file_filenames = get_image_attachments(message.attachments)
            await message.delete()

            if settings['filter']:
                response = classify.imageClassifyUrl(urls=image_urls)
                predictions = response['Prediction']

                if settings['spoiler']:
                    # ADD SPOILER TAG TO NUDE OR SEXY IMAGES.
                    for index, prediction in enumerate(predictions):
                        response = requests.get(image_urls[index], stream=True)
                        data = BytesIO(response.content)
                        if prediction['class'] == "nude":
                            files.append(discord.File(data, filename=image_filenames[index], spoiler=True))
                        elif prediction['class'] == "sexy" and settings['include_sexy']:
                            files.append(discord.File(data, filename=image_filenames[index], spoiler=True))
                        elif prediction['class'] == "safe":
                            files.append(discord.File(data, filename=image_filenames[index]))
                    await message.channel.send("Posted by: {}".format(author), files = files)
                        
                else:
                    # UPLOAD ONLY SAFE IMAGES
                    for index, prediction in enumerate(predictions):
                        if prediction['class'] == "nude":
                            nude_counter += 1
                        else:
                            safe_urls.append(image_urls[index])
                            safe_filenames.append(image_filenames[index])
                    
                    for index, url in enumerate(safe_urls):
                        response = requests.get(url, stream=True)
                        data = BytesIO(response.content)
                        files.append(discord.File(data, filename=safe_filenames[index]))

                    message_string = "Posted by: {}".format(author)
                    if nude_counter > 0:
                        message_string = message_string + " {} image(s) contains nudity.".format(nude_counter)
                    await message.channel.send(message_string, files = files)

            elif settings['censor']:
                response = detect.detectExposedFromUrl(urls=image_urls)
                predictions = response['Prediction']
                for index, prediction in enumerate(response['Prediction']):
                    data = censor_image(prediction)
                    files.append(discord.File(data, filename=image_filenames[index]))
                message_string = "Posted by: {}".format(author)
                await message.channel.send(message_string, files = files)
            
            for index, unsupported_url in enumerate(unsupported_file_urls):
                response = requests.get(unsupported_url)
                unsupported_files = discord.File(BytesIO(response.content), filename=unsupported_file_filenames[index])
                await message.channel.send(file=unsupported_files)
            
        await bot.process_commands(message)        

bot.run(TOKEN)
