from discord import Embed, Color

def format_embed(title, description):
    if description == "":
        embed = Embed(title=title, color=Color.random())

    else:
        embed = Embed(title=title, description=description, color=Color.random())

    return embed
