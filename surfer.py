import discord
import random
import json
import math
from discord.ext import commands, tasks
from discord.utils import get
client = commands.Bot(command_prefix = "v/")
client.remove_command('help')

g = {}

@tasks.loop(seconds=3)
async def check():
    for guild in client.guilds:
        await adjust_activity(guild)
        await add_xp(guild,max(0,math.floor(g["Activity"][str(guild.id)]/(10*g["Level"][str(guild.id)]))))
    print('Check')

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("v/surf"),status=discord.Status.online)

    global g
    with open('guilds.json','r') as i:
        g = json.load(i)
        i.close()

    for guild in client.guilds:
        if guild.id not in g["Guilds"]:
            await add_serv(guild.id)
        g["VoiceUsers"][str(guild.id)] = await vc_count(guild)
        await adjust_activity(guild)

    for guild in g["Guilds"]:
        if client.get_guild(guild) not in client.guilds:
            await remove_serv(guild)
    
    check.start()


    print("Bot Ready")

@client.event
async def on_voice_state_update(member, before, after):
    act = g["Activity"][str(member.guild.id)]
    if before.channel==None and after.channel!=None and after.channel.permissions_for(member.guild.me).view_channel:
        g["Activity"][str(member.guild.id)] += (len(member.guild.members)+math.floor((act+1)/(2*len(member.guild.members))))*g["Level"][str(member.guild.id)]
        g["VoiceUsers"][str(member.guild.id)] += 1
    if after.channel==None and before.channel!=None and before.channel.permissions_for(member.guild.me).view_channel:
        g["Activity"][str(member.guild.id)] = max(0, g["Activity"][str(member.guild.id)]-(len(member.guild.members)+math.floor((act+1)/(2*len(member.guild.members))))*g["Level"][str(member.guild.id)])
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
async def activity(ctx):
    await ctx.send(f'Server Activity: {max(0,g["Activity"][str(ctx.guild.id)])}')

@client.command(pass_context = True)
async def level(ctx):
    await ctx.send(f'Server VC Level: {g["Level"][str(ctx.guild.id)]}')

@client.command(pass_context=True)
async def surf(ctx):
    if client.get_guild(g["Guilds"][0])==ctx.guild:
        guild = client.get_guild(g["Guilds"][1])
    else:
        guild = client.get_guild(g["Guilds"][0])
    
    if g["Activity"][str(guild.id)]==0:
        await ctx.send("There are no active servers")
    else:
        await ctx.send(g["Invites"][str(guild.id)])

@client.command(pass_context=True)
async def masterlist(ctx):
    if ctx.author.id==354452150316957696:
        global g
        disp = ""
        for i in g["Guilds"]:
            amt = 0
            guild = client.get_guild(i)
            

            disp += f'{guild.name} - {g["Invites"][str(i)][-6]} - {g["VoiceUsers"][str(i)]}\n'
        await ctx.send(f'```{disp}```')

@client.command(pass_context=True)
async def leaderboard(ctx):
    global g
    disp = "Most Active Servers"
    for i in g["Guilds"][:10]:
        amt = 0
        guild = client.get_guild(i)
        if g["Invites"][str(i)]=="null":
            invite = g["Invites"][str(i)]
        else:
            invite = g["Invites"][str(i)][-6:]
        

        disp += f'\nServer: {guild.name} - Invite: {invite} - Activity: {max(0,g["Activity"][str(i)])}'
    await ctx.send(f'```{disp}```')

@client.command(pass_context=True)
async def levelChannel(ctx):
    g["LevelChannel"][str(ctx.guild.id)] = ctx.channel.id
    await ctx.send(f'VC Level changes will now be posted in {ctx.channel.name}')

@client.command(pass_context=True)
async def setInvite(ctx, invite:discord.Invite):
    try:
        g["Invites"][str(ctx.guild.id)] = str(invite)
    except:
        await ctx.send("No invite or an invalid invite was sent")

@client.command(pass_contect=True)
async def help(ctx):
    await help_embed(ctx.channel)

@client.command(pass_context=True)
async def test_embed(ctx):
    await vc_embed(ctx.channel)

async def remove_serv(id):
    global g
    g["Servers"] -= 1
    g["Guilds"].remove(id)
    g["VoiceUsers"].pop(str(id))
    g["Invites"].pop(str(id))
    g["XP"].pop(str(id))
    g["Level"].pop(str(id))
    g["LevelChannel"].pop(str(id))
    await commit()
    print(f'Removed {id}')

async def add_serv(id):
    global g
    g["Servers"] += 1
    g["Guilds"].append(id)
    g["XP"][str(id)] = 0
    g["Activity"][str(id)] = 0
    g["Level"][str(id)] = 1
    try:
        g["Invites"][str(id)] = await make_invite(client.get_guild(id))
    except:
        g["Invites"][str(id)] = "null"
    await commit()

    text = await get_text(client.get_guild(id))
    await vc_embed(text)

    print(f'Added {id}')

async def vc_count(guild):
    amt = 0
    for j in guild.voice_channels:
        if j.permissions_for(guild.me).view_channel:
            amt += len(j.members)
    return amt

async def make_invite(guild):
    text = await get_text(guild)
    invite = str(await text.create_invite())
    return invite

async def adjust_activity(guild):
    act = g["Activity"][str(guild.id)]
    if g["VoiceUsers"][str(guild.id)]==0:
        g["Activity"][str(guild.id)] = 0
    elif act>=0 and len(guild.members)>10:
        g["Activity"][str(guild.id)] = max(g["VoiceUsers"][str(guild.id)]*(15+g["Level"][str(guild.id)]),g["Activity"][str(guild.id)] + g["VoiceUsers"][str(guild.id)]*10*g["Level"][str(guild.id)]-(len(guild.members)+math.floor((act+1)/len(guild.members))))
    elif act>=0 and len(guild.members)<=10:
        g["Activity"][str(guild.id)] = max(g["VoiceUsers"][str(guild.id)]*10,g["Activity"][str(guild.id)]+g["VoiceUsers"][str(guild.id)]*10-(len(guild.members)+math.floor((act+1)/len(guild.members))))
    else:
        g["Activity"][str(guild.id)] = g["VoiceUsers"][str(guild.id)]
    g["Guilds"].sort(key=active_sort,reverse=True)
    await commit()

async def add_xp(guild, xp):
    g["XP"][str(guild.id)] += xp
    if g["XP"][str(guild.id)]/(1500*g["Level"][str(guild.id)]) > g["Level"][str(guild.id)]:
        await level_up(guild)
    await commit()

async def level_up(guild):
    g["XP"][str(guild.id)] = 0
    if g["Level"][str(guild.id)]<10:
        g["Level"][str(guild.id)] += 1
        if str(guild.id) in g["LevelChannel"].keys():
            await guild.get_channel(g["LevelChannel"][str(guild.id)]).send(f'{guild.name} is now level {g["Level"][str(guild.id)]}')

async def get_text(guild):
    for i in guild.text_channels:
        if i.permissions_for(guild.me).send_messages:
            text = i
            break
    return text

async def vc_embed(text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name="VC Surfer",icon_url=client.user.avatar_url)
    embed.add_field(name="v/surf",value="```Find active vc```",inline=True)
    embed.add_field(name="v/leaderboard",value="```List of most active servers```",inline=True)
    embed.add_field(name="v/help",value="```More commands```",inline=True)
    await text.send(embed=embed)
    if g["Invites"][str(text.guild.id)]=="null":
        await text.send("An invite could not be set: Use v/setInvite to set one")

async def help_embed(text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name="VC Surfer",icon_url=client.user.avatar_url)
    embed.add_field(name="v/surf",value="```Find servers with active vcs```",inline=True)
    embed.add_field(name="v/leaderboard",value="```Get list of most active servers```",inline=True)
    embed.add_field(name="v/setInvite",value="```Set the invite that the bot sends```",inline=True)
    embed.add_field(name="v/levelChannel",value="```Set this channel for vc level ups```",inline=True)
    embed.add_field(name="v/activity",value="```Get server's current activity```",inline=True)
    embed.add_field(name="v/level",value="```Get server's current vc level```",inline=True)
    await text.send(embed=embed)

async def commit():
    with open('guilds.json','w') as i:
        i.write(json.dumps(g, indent=1))
        i.close()

def active_sort(id):
    return g["Activity"][str(id)]

client.run('NzQwMDY0MzQ0NjExNzQ5OTI4.XyjkoQ.MJyt8yoIrKCIfjNP583TcZKZZCQ')
