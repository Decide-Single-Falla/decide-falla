# Created by JStockwell on GitHub
import os
import json
import asyncio

import discord
import Paginator
import requests

import utils.formatter as Formatter
from utils.help import help_command

from discord.ext import commands
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
bot.remove_command('help')

if DEV_MODE:
    test_votes = json.load(open('dev_templates/votes.json', 'r'))["votes"]

### --- Functions --- ###

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    bot_channel = bot.get_channel(1159533434423738403)
    await bot_channel.send("Bot is online!")

    if DECIDE_MODE:
        try:
            init_ping = requests.get(f'{BASE_URL}/admin/login/', timeout=10)
        except requests.exceptions.Timeout:
            print("Init process failed!")

        try:
            if init_ping.status_code == 200:
                print("Init process complete!")

            else:
                print("Init process failed!")
                exit()
        except requests.exceptions.HTTPError as err:
            print("Init process failed: " + str(err))
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
        message += 'An error has occurred.\nIf you want to know the available commands, use !help'

    print(error)
    await ctx.send(message)

### --- Commands --- ###

@bot.command(name="hello", help="How are you?")
async def hello(ctx):
    await ctx.send("Hello!")

@bot.command(name="help", help="Get help")
async def help(ctx, *args):
    if len(args) == 0:
        embed = discord.Embed(title="List of commands", color=0x00ff00)
        embed.add_field(name="", value="If you need to know more about a command, use !help <command>", inline=False)
        for command in bot.commands:
            if command.name != "help":
                embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)
    else:
        bot_command = None
        for command in bot.commands:
            if command.name == args[0]:
                bot_command = command
                break

        if bot_command is None:
            await ctx.send("Command not found")
        else:
            await help_command(ctx, bot_command)

# @bot.command(name="get_voting", help="Get a voting")
# async def get_voting(ctx, *args):
#     # TODO LIST
#     # Message others when they react
#     # Delete or lock message after time ?

#     if len(args) == 0:
#         await ctx.send("Please provide a voting ID!")
#         return

#     voting_id = int(args[0])
#     voting = test_votes[voting_id]

#     # TODO Add error message for wrong reaction
#     def check(r: discord.Reaction, u: Union[discord.Member, discord.User]):
#         return u.id == ctx.author.id and r.message.channel.id == ctx.channel.id and r.message.id == msg.id and \
#                emotes.index(str(r.emoji)) - 1 < counter

#     embed = Formatter.format_embed(voting["title"], voting["description"])

#     # Reaction lookup table
#     emotes = ["0️⃣","1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

#     counter = 1
#     for option in voting["options"]:
#         embed.add_field(name=emotes[counter], value=option, inline=False)
#         counter += 1

#     msg = await ctx.send(embed=embed)

#     # TODO React to reactions
#     for i in range(1,counter):
#         await msg.add_reaction(emotes[i])

#     try:
#         reaction = await bot.wait_for('reaction_add', check = check, timeout = 60.0)
#     except asyncio.TimeoutError:
#         # at this point, the check didn't become True.
#         await ctx.send(f"**{ctx.author}**, you didnt react correctly with within 60 seconds.")
#         return
#     else:
#         # at this point, the check has become True and the wait_for has done its work, now we can do ours.
#         # here we are sending some text based on the reaction we detected.
#         await post_voting(ctx, reaction, voting, emotes.index(reaction[0].emoji) - 1)
#         return

# We will retrieve the voting from the data base using the id. f.e !get_voting_by_id 2
@bot.command(name="get_voting_by_id", help="Get a voting by ID")
async def get_voting_by_id(ctx, *args):
    if len(args) == 0:
        await ctx.send("Please provide a voting ID!")
        return

    voting_id = int(args[0])
    response = requests.get(BASE_URL + "voting/details/" + str(voting_id) + "/", timeout=5)
    voting = response.json()

    def check(r: discord.Reaction, u: Union[discord.Member, discord.User]):
        return u.id == ctx.author.id and r.message.channel.id == ctx.channel.id and r.message.id == msg.id and \
               emotes.index(str(r.emoji)) - 1 < counter

    embed = discord.Embed(title=voting["name"], color=discord.Color.random())

    emotes = ["0️⃣","1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    counter = 1
    options = voting["question"]["options"]
    for option in options:
        embed.add_field(name=emotes[counter], value=f"{option['number']}. {option['option']}", inline=False)
        counter += 1

    msg = await ctx.send(embed=embed)

    for i in range(1,counter):
        await msg.add_reaction(emotes[i])

    try:
        reaction = await bot.wait_for('reaction_add', check = check, timeout = 60.0)
    except asyncio.TimeoutError:
        await ctx.send(f"**{ctx.author}**, you didnt react correctly with within 60 seconds.")
        return
    else:
        await post_voting(ctx, reaction, voting, emotes.index(reaction[0].emoji) - 1)
        return

@bot.command(name="list_active_votings", help="List all votings")
async def list_active_votings(ctx):
    response = requests.get(BASE_URL + "voting/", timeout=5)
    votings = response.json()
    embeds = format_votings_list(votings)
    await Paginator.Simple().start(ctx, pages=embeds)

@bot.command(name="list_all_votings", help="List active votings")
async def list_all_votings(ctx):
    response = requests.get(BASE_URL + "voting/", timeout=5)
    votings = response.json()
    embeds = format_votings_list(votings)
    await Paginator.Simple().start(ctx, pages=embeds)

def format_votings_list(votings):
    embeds = []

    # TODO Make recursive
    counter = 0
    while (counter < len(votings)):
        voting = votings[counter]
        embed = discord.Embed(title='Votings', color=discord.Color.random())
        embed.add_field(name=f'{voting["id"]}: {voting["name"]}', value=voting["question"]["desc"], inline=False)
        counter += 1

        if counter < len(votings):
            voting = votings[counter]
            embed.add_field(name=f'{voting["id"]}: {voting["name"]}', value=voting["question"]["desc"], inline=False)
            counter += 1

            if counter < len(votings):
                voting = votings[counter]
                embed.add_field(name=f'{voting["id"]}: {voting["name"]}', value=voting["question"]["desc"], inline=False)
                counter += 1

        embeds.append(embed)

    return embeds

async def post_voting(ctx, reaction, voting, selected_option):
    discord_voter_id = ctx.author.id
    voting_id = voting["id"]
    selected_option = selected_option

    print("ctx es: ", ctx)
    print("ctx_autor es: ", ctx.author)

    print("Voter_id es: ", discord_voter_id)
    # voter_id = 1
    print("Voting_id es: ", voting_id)
    print("Selected_option es: ", selected_option)

    # List = [username, password]
    credentials = await private_message_to_login(ctx, msg="Hello")
    token = login_user(credentials[0], credentials[1])

    url = f'{BASE_URL}store/discord/{voting_id}/{discord_voter_id}/{selected_option}/'
    # TODO get token with login
    response = requests.post(url, timeout=5)

    #print("Url es: ", url)
    #print("Response es: ", response)
    #print("Status code es: ", response.status_code)
    
    if response.status_code == 200:
        await ctx.send(f"**{ctx.author}**, your vote has been recorded. You voted for option {str(reaction[0].emoji)}")
    else:
        await ctx.send(f"**{ctx.author}**, there was an error recording your vote.")

async def private_message_to_login(ctx,msg):
    userid = ctx.author.id
    user = bot.get_user(userid)
    await user.send(f'Buenas {ctx.author}, por favor, mándeme sus credenciales (usuario y contraseña) en dos mensajes separados, primero el usuario y después la contraseña.\n\nUna vez mandado los credenciales, borre el mensaje por su seguridad.\n\nPor favor, mande su usuario')
    username = await bot.wait_for('message', check=lambda message: message.author.id == userid and isinstance(message.channel, discord.DMChannel), timeout=30)
    await user.send("Por favor, mande su contraseña")
    password = await bot.wait_for('message', check=lambda message: message.author.id == userid and isinstance(message.channel, discord.DMChannel), timeout=30)
    await user.send(f'{username.content} with password {password.content} has been stolen.')

    return [username.content, password.content]

def login_user(username, password):
    data = {'username': username, 'password': password}
    response = requests.post(f'{BASE_URL}authentication/login/', data=data)
    login_token = response['token']
    return login_token

### --- Run Bot --- ###

bot.run(TOKEN)