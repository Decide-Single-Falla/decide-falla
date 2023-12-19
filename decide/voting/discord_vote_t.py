import discord
import requests
import pytest
import pytest_asyncio
from discord.ext import commands
from discord.ext.commands import Cog, command
import discord.ext.test as dpytest
from discord import Embed, Color
from dotenv import load_dotenv
from typing import Union

load_dotenv()

BASE_URL = 'http://localhost:8000/'

@pytest_asyncio.fixture
async def bot():
   # Setup
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    await b._async_setup_hook()

    dpytest.configure(b)

    yield b

    # Teardown
    await dpytest.empty_queue() # empty the global message queue as test teardown

async def post_voting(username, password):
    token = login_user(username, password)

    get_user = f'{BASE_URL}authentication/getuser/'

    headers = {'Accept': 'application/json'}
    print(token)
    data={'token': str(token['token'])}

    response = requests.post(get_user, headers=headers, json=data, timeout=10).json()
    discord_voter_id = response['id']

    #primero comprobamos que está en el census:
    census_url = f'{BASE_URL}census/list/1/'
    response_census = requests.get(census_url, timeout=10)

    if not check_census(response_census.json(), discord_voter_id):
        return False
    
    else:
        url = f'{BASE_URL}store/discord/1/{discord_voter_id}/1/'
        response = requests.post(url, headers=headers,json=data, timeout=10)

        if response.status_code == 200:
            return True
        else:
            return False

def check_census(response, userid):
    user_list = []

    for census in response:
        user_list.append(str(census['voter_id']))

    return str(userid) in user_list

def login_user(username, password):
    data = {'username': username, 'password': password}
    response = requests.post(f'{BASE_URL}authentication/login/', data=data, timeout=10)
    login_token = response.json()
    return login_token

############# WORKING TESTS ############# 

# Para ejecutar este test debemos situarnos en la ruta del test y ejecutar 'pytest discord_t.py'

def test_login(bot):
    token = login_user('testuser', 'testpassword')
    assert isinstance(token, dict) and isinstance(token['token'], str)

def test_login_fail(bot):
    response = login_user('nottestuser', 'nottestpassword')
    assert response['non_field_errors'][0] == 'Unable to log in with provided credentials.'

# Para que el test funcione debe existir un usuario testuser y que este en el censo de la pregunta 1
@pytest.mark.asyncio
async def test_vote(bot):
    assert await post_voting('testuser', 'testpassword')