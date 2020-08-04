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
        g["VoiceUsers"][str(guild.id)]= await vc_count(guild)

    for guild in g["Guilds"]:
        if client.get_guild(guild) not in client.guilds:
            await remove_serv(guild)
        


    print("Bot Ready")

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel==None and after.channel!=None:
        g["Guilds"].insert(0,g["Guilds"].pop(g["Guilds"].index(member.guild.id)))
        g["VoiceUsers"][str(member.guild.id)] += 1
    if after.channel==None and before.channel!=None:
        g["Guilds"].insert(g["Guilds"].index(member.guild.id)+1,g["Guilds"].pop(g["Guilds"].index(member.guild.id)))
        g["VoiceUsers"][str(member.guild.id)] -= 1
    await commit()

@client.event
async def on_guild_join(guild):
    await add_serv(guild.id)

@client.event
async def on_guild_remove(guild):
    await remove_serv(guild.id)

@client.event
async def on_disconnect():
    global g
    await commit()

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
    await ctx.send(g["Invites"][str(guild.id)])

@client.command(pass_context=True)
async def masterlist(ctx):
    global g
    disp = ""
    for i in g["Guilds"]:
        amt = 0
        guild = client.get_guild(i)
        

        disp += f'{guild.name} - {g["Invites"][str(i)][19:]} - {g["VoiceUsers"][str(i)]}\n'
    await ctx.send(f'```{disp}```')

async def remove_serv(id):
    global g
    g["Servers"] -= 1
    g["Guilds"].remove(id)
    g["VoiceUsers"].remove(str(id))
    g["Invites"].remove(str(id))
    await commit()
    print(f'Removed {id}')

async def add_serv(id):
    global g
    g["Servers"] += 1
    g["Guilds"].append(id) 
    g["Invites"][str(id)] = await make_invite(client.get_guild(id))
    await commit()
    print(f'Added {id}')

async def vc_count(guild):
    amt = 0
    for j in guild.voice_channels:
        amt += len(j.members)
    return amt

async def make_invite(guild):
    for i in guild.text_channels:
        if i.permissions_for(guild.me).send_messages:
            text = i
            break
    invite = str(await text.create_invite())
    return invite

async def commit():
    with open('guilds.json','w') as i:
        i.write(json.dumps(g, indent=1))
        i.close()

client.run(TOKEN)
