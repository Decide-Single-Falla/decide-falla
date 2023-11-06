# Created by JStockwell on GitHub
import os
import json
import asyncio

import discord
import Paginator
import requests
import utils.formatter as Formatter

from discord.ext import commands, tasks
from dotenv import load_dotenv

from typing import Union

load_dotenv()

### --- REST api Initialization --- ###

BASE_URL = os.getenv('BASE_URL')

### --- Bot Initialization --- ###

TOKEN = os.getenv('DISCORD_TOKEN')
DEV_MODE = os.getenv('DEV_MODE') == 'TRUE'
DECIDE_MODE = os.getenv('DECIDE_MODE') == 'TRUE'

GEN_DB_FLAG = False

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
#bot.remove_command('help')
if DEV_MODE:
    test_votes = json.load(open('dev_templates/votes.json', 'r'))["votes"]

### --- Functions --- ###

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    bot_channel = bot.get_channel(1159533434423738403)
    await bot_channel.send("Bot is online!")

    if DECIDE_MODE:
        init_ping = requests.get(f'{BASE_URL}/admin/login/')

        try:
            if init_ping.status_code == 200:
                print("Init process complete!")

            else:
                print("Init process failed!")
                exit()
        except:
            print("Init process failed!")
            exit()

@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise ValueError(f'Unhandled event: {event}')

@bot.event
async def on_command_error(ctx, error):
    message = " "

    if DEV_MODE:
        message += f'\n{error}'
    else:
        message += f'An error has occurred, please try again!'

    print(error)
    await ctx.send(message)

### --- Commands --- ###

@bot.command(name="hello", help="How are you?")
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command(name="get_voting", help="Get a voting")
async def get_voting(ctx, *args):
    # TODO LIST
    # React to reactions
    # Stop after x time
    # Message others when they react
    # Delete or lock message after time ?

    if len(args) == 0:
        await ctx.send("Please provide a voting ID!")
        return

    voting_id = int(args[0])
    vote = test_votes[voting_id]
    option_numbers = []

    def check(r: discord.Reaction, u: Union[discord.Member, discord.User]):
        return u.id == ctx.author.id and r.message.channel.id == ctx.channel.id and r.message.id == msg.id and \
               emotes.index(str(r.emoji)) - 1 in range(len(option_numbers))

    embed = Formatter.format_embed(vote["title"], vote["description"])

    # Reaction lookup table
    emotes = ["0️⃣","1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    counter = 1
    for option in vote["options"]:
        embed.add_field(name=emotes[counter], value=option, inline=False)
        counter += 1

    msg = await ctx.send(embed=embed)

    # TODO React to reactions
    for i in range(1,counter):
        await msg.add_reaction(emotes[i])

    try:
        reaction = await bot.wait_for('reaction_add', check = check, timeout = 60.0)
    except asyncio.TimeoutError:
        # at this point, the check didn't become True.
        await ctx.send(f"**{ctx.author}**, you didnt react correctly with within 60 seconds.")
        return

### --- Run Bot --- ###

bot.run(TOKEN)