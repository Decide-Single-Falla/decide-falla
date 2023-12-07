import discord
import requests
import pytest
import pytest_asyncio
from discord.ext import commands
from discord.ext.commands import Cog, command
import discord.ext.test as dpytest
from discord import Embed, Color
from dotenv import load_dotenv

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decide.settings')
django.setup()

from .models import Voting

load_dotenv()

BASE_URL = 'http://localhost:8000/'

class Misc(Cog):
    @command()
    async def list_all_votings(self, ctx):
        response = requests.get(BASE_URL + "voting/", timeout=5)
        votings = response.json()
        embed = Embed(title='Votings', color=Color.random())
        for voting in votings:
            embed.add_field(name=f'{voting["id"]}: {voting["name"]}',
                             value=voting["question"]["desc"], inline=False)
        await ctx.send(embed=embed)

@pytest_asyncio.fixture
async def bot():
    # Setup
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    await b._async_setup_hook()
    await b.add_cog(Misc())

    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue() # empty the global message queue as test teardown

############# TEST ############# DONE

#TODO: Create a votation in the database and test the list_all_votings command

@pytest.mark.asyncio
async def test_list_all_votings(bot):
    await dpytest.message("!list_all_votings")
    title = dpytest.get_embed().title
    assert "Votings" in title


# Fake test

@pytest.mark.asyncio
async def test_embed_peek(bot):
    guild = bot.guilds[0]
    channel = guild.text_channels[0]

    embed = discord.Embed(title="Test Embed")
    embed.add_field(name="Field 1", value="Lorem ipsum")

    embed2 = embed = discord.Embed(title="Test Embed")
    embed2.add_field(name="Field 1", value="Lorem ipsum")

    await channel.send(embed=embed)

    # peek option doesn't remove the message fro the queue
    assert dpytest.verify().message().peek().embed(embed2)
    # verify_embed (without peek) WILL remove emebd from the queue
    assert dpytest.verify().message().embed(embed2)    


@pytest.fixture
def voting(db):
    voting = Voting.objects.create(name="Test Voting", description="This is a test voting")
    print("Voting created: ", voting)
    return voting

@pytest.mark.asyncio
async def test_list_all_votings(bot):
    await dpytest.message("!list_all_votings")
    response = dpytest.get_message()
    embed = response.embeds[0]
    print("Embed es: ", embed)
    print("Embed to dict es: ", embed.to_dict())
    assert embed.title == "Votings"
    # embed is: {'fields': [{'inline': False, 'name': '2: Mejor juego del año', 'value': 'Cual es el mejor juego del año'}, {'inline': False, 'name': '3: peor juego del año', 'value': 'peor juego del año'}, {'inline': False, 'name': '4: voy a aprobar?', 'value': 'voy a aprobar'}], 'color': 16736000, 'type': 'rich', 'title': 'Votings'}
    # assert embed.