import discord
import requests
import pytest
import pytest_asyncio

from discord.ext import commands
from discord.ext.commands import Cog, command
import discord.ext.test as dpytest

from discord import Embed, Color
from dotenv import load_dotenv

from test_utils.help import help_command

bot_commands = [
    {
        "name": "get_voting",
        "help": "Get a voting"
    },
    {
        "name": "list_all_votings",
        "help": "List all votings"
    },
    {
        "name": "list_active_votings",
        "help": "List active votings"
    },
    {
        "name": "hello",
        "help": "How are you?"
    } 
]

class Misc(Cog):
    @command()
    async def help(self, ctx, *args):
        if len(args) == 0:
            embed = discord.Embed(title="List of commands", color=0x00ff00)
            embed.add_field(name="", value="If you need to know more about a command, use !help <command>", inline=False)
            for command in bot_commands:
                if command['name'] != "help":
                    embed.add_field(name=command['name'], value=command['help'], inline=False)
            await ctx.send(embed=embed)
        else:
            bot_command = None
            for command in bot_commands:
                if command['name'] == args[0]:
                    bot_command = command
                    break

            if bot_command is None:
                await ctx.send("Command not found")
            else:
                await help_command(ctx, bot_command)

@pytest_asyncio.fixture
async def bot():
    # Setup
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    await b._async_setup_hook()
    b.remove_command("help")
    await b.add_cog(Misc())

    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue() # empty the global message queue as test teardown

@pytest.mark.asyncio
async def test_help(bot):
    await dpytest.message("!help")
    response = dpytest.get_message()
    print(response)
    embed = response.embeds[0]
    assert embed.title == "List of commands"
    assert embed.fields[0].value == "If you need to know more about a command, use !help <command>"
    assert embed.fields[1].name == "get_voting"
    assert embed.fields[1].value == "Get a voting"
    assert embed.fields[2].name == "list_all_votings"
    assert embed.fields[2].value == "List all votings"
    assert embed.fields[3].name == "list_active_votings"
    assert embed.fields[3].value == "List active votings"
    assert embed.fields[4].name == "hello"
    assert embed.fields[4].value == "How are you?"

@pytest.mark.asyncio
async def test_help_arg_correct(bot):
    await dpytest.message("!help get_voting")
    response = dpytest.get_message()
    embed = response.embeds[0]
    assert embed.title == "!get_voting: Buscar Voto"
    assert embed.fields[0].value == "Busca el voto con el ID dado para poder votar."
    assert embed.fields[1].value == "Formato: !get_votes <ID>"

@pytest.mark.asyncio
async def test_help_arg_incorrect(bot):
    await dpytest.message("!help incorrect_arg")
    assert dpytest.verify().message().content("Command not found")