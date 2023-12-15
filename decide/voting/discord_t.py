import discord
import requests
import pytest
import pytest_asyncio
from discord.ext import commands
from discord.ext.commands import Cog, command
import discord.ext.test as dpytest
from discord import Embed, Color
from dotenv import load_dotenv

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

############# TEST ############# 

# Este es un test que he intentado hacer para comprobar que el bot recupera correctamente de la base de datos
# el problema es que django es sincrono y el bot asincrono, no soy capaz de recuperar la información creada
# durante la ejecución del test para integrar la prueba automaticamente con decide.
# para poder ejecutar el test y ver que funciona con nuestros datos locales, debemos de ejecutar en la ruta del test
# 'pytest discord_t.py' se le puede añadir -s para más información
# ahí podemos ver como si en el assert embed.fields[0].name ponemos el 'id: nombre' de la votación que hemos creado
# en la base de datos, el test funciona correctamente

# Get all votings from the database
@pytest.fixture(scope='module')
def voting(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        question = Question.objects.create(desc="Question desc")
        question.save()
        for i in range(3):
            option = QuestionOption(question=question, option='option {}'.format(i+1))
            option.save()
        voting = Voting.objects.create(name="Test Voting", desc="This is a test voting", question=question)
        voting.save()
        votings = Voting.objects.all()
        for votingg in votings:
            print("Voting: ", votingg)
        return voting

@pytest.mark.asyncio
async def test_list_all_votings(bot):
    await dpytest.message("!list_all_votings")
    response = dpytest.get_message()
    embed = response.embeds[0]
    print("Embed: ", embed)
    print("Voting es: ", voting)
    # print("Votación por parametro: ", voting.question.desc)
    print("Embed to dict: ", embed.to_dict()) # print para ver qué votaciones tenemos en base de datos
    assert embed.title == "Votings"
    assert embed.fields[0].name == "2: Votación para el bot"
