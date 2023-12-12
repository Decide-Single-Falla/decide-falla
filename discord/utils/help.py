import discord

from utils.switch import switch, case

async def help_command(ctx, command):
    while switch(command.name):
        if case("hello"):
            await generic_help(ctx, command, "Hello", ["Why do you need help with a simple hello? :("])
            break
        if case("help"):
            await generic_help(ctx, command, "h e l p", ["I am in your walls.", "I am in your dreams.", "I am in your... help?"])
            break
        if case("get_voting"):
            await generic_help(ctx, command, "Buscar Voto", ["Busca el voto con el ID dado para poder votar.", "Formato: !get_votes <ID>"])
            break
        if case("list_all_votings"):
            await generic_help(ctx, command, "Listar Todos los Votos", ["Devuelve una lista con todos los votos.", "Formato: !list_all_votings"])
            break
        if case("list_active_votings"):
            await generic_help(ctx, command, "Listar Votos Activos", ["Devuelve una lista con todos los votos activos.", "Formato: !list_active_votings"])
            break
        else:
            await generic_help(ctx, command, command.name, [command.help])
            break

async def generic_help(ctx, command, title, description):
    embed = discord.Embed(title=f"!{command.name}: {title}", color=0x00ff00)
    for field in description:
        embed.add_field(name="", value=field, inline=False)
    await ctx.send(embed=embed)