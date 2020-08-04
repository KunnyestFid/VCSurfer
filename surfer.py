import discord
import random
import json
from discord.ext import commands, tasks
from discord.utils import get
client = commands.Bot(command_prefix = "v/")

g = {}

@client.event
async def on_ready():

    await client.change_presence(activity=discord.Game("v/surf"))

    global g
    with open('guilds.json','r') as i:
        g = json.load(i)
        i.close()

    for guild in client.guilds:
        if guild.id not in g["Guilds"]:
            await add_serv(guild.id)

    for guild in g["Guilds"]:
        if client.get_guild(guild) not in client.guilds:
            await remove_serv(guild)


    print("Bot Ready")

@client.event
async def on_voice_state_update(member, before, after):
    if (before.channel==None or before.channel!=after.channel) and after.channel!=None:
        g["Guilds"].insert(0,g["Guilds"].pop(g["Guilds"].index(member.guild.id)))
        with open('guilds.json','w') as i:
            i.write(json.dumps(g))
            i.close()

@client.event
async def on_guild_join(guild):
    await add_serv(guild.id)

@client.event
async def on_guild_remove(guild):
    await remove_serv(guild.id)

@client.event
async def on_disconnect():
    global g
    with open('guilds.json','w') as i:
        i.write(json.dumps(g))
        i.close()

@client.command(pass_context=True)
async def surf(ctx):
    if client.get_guild(g["Guilds"][0])==ctx.guild:
        guild = client.get_guild(g["Guilds"][1])
    else:
        guild = client.get_guild(g["Guilds"][0])
    
    for i in guild.text_channels:
        if i.permissions_for(guild.me).send_messages:
            text = i
            break
    await ctx.send(str(await text.create_invite()))

async def remove_serv(id):
    global g
    g["Servers"] -= 1
    g["Guilds"].remove(id) 
    with open('guilds.json','w') as i:
        i.write(json.dumps(g))
        i.close()
    print(f'Removed {id}')

async def add_serv(id):
    global g
    g["Servers"] += 1
    g["Guilds"].append(id) 
    with open('guilds.json','w') as i:
        i.write(json.dumps(g))
        i.close()
    print(f'Added {id}')

client.run(REDACTED)
