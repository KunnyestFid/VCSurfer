import discord
import random
import json
import math
from discord.ext import commands, tasks
from discord.utils import get
client = commands.Bot(command_prefix = "v/")
client.remove_command('help')

kunny = [354452150316957696, 301593613832290304, 354386735414640650]
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
        g["VoiceUsers"][str(guild.id)] = await vc_count(guild)
        if guild.id not in g["Guilds"]:
            await add_serv(guild.id)
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
        g["Activity"][str(member.guild.id)] = max(g["VoiceUsers"][str(member.guild.id)]*(15+g["Level"][str(member.guild.id)]), g["Activity"][str(member.guild.id)]-(len(member.guild.members)+math.floor((act+1)/(2*len(member.guild.members))))*g["Level"][str(member.guild.id)])
        g["VoiceUsers"][str(member.guild.id)] -= 1
    if g["VoiceUsers"][str(member.guild.id)] < 0:
        g["VoiceUsers"][str(member.guild.id)] = await vc_count(member.guild)
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
async def push_update(ctx, update):
    if ctx.author.id in kunny:
        a = []
        for i in client.guilds:
            if i.owner not in a:
                a.append(i.owner)
        for j in a:
            try:
                j.dm_channel.send(update)
            except:
                j.create_dm()
                j.dm_channel.send(update) 

@client.command(pass_context=True)
async def activity(ctx):
    await ctx.send(f'**Server Activity:** {max(0,g["Activity"][str(ctx.guild.id)])}')

@client.command(pass_context = True)
async def level(ctx):
    if g["Level"][str(ctx.guild.id)]<10:
        percent = math.floor(g["XP"][str(ctx.guild.id)]/(1500*g["Level"][str(ctx.guild.id)]*g["Level"][str(ctx.guild.id)])*100)
        await ctx.send(f'**Server VC Level:** {g["Level"][str(ctx.guild.id)]} [{percent}% to next level]')
    else:
        await ctx.send(f'**Server VC Level:** 10 [MAX LEVEL]')
@client.command(pass_context=True)
async def surf(ctx, category=None):
    guild = 0
    for i in g["Guilds"]:
        if str(i) not in g["Categories"].keys():
            g["Categories"][str(i)] = None
        if g["Activity"][str(i)]==0 or (client.get_guild(i)!=ctx.guild and (category==None or category==g["Categories"][str(i)])):
            guild = client.get_guild(i)
            break

        
    if g["Activity"][str(guild.id)]!=0:
        await ctx.send(g["Invites"][str(guild.id)])
        await guild_embed(guild,ctx.channel)
    else:
        await ctx.send("No active servers could be found")
        


@client.command(pass_context=True)
async def masterlist(ctx):
    if ctx.author.id in kunny:
        global g
        disp = ""
        for i in g["Guilds"]:
            amt = 0
            guild = client.get_guild(i)
            

            disp += f'{guild.name} - {g["Invites"][str(i)][-7:]} - {g["Activity"][str(i)]}\n'
        await ctx.send(f'```{disp}```')

@client.command(pass_context=True)
async def leaderboard(ctx):
    global g
    a = []
    b = 0
    for i in g["Guilds"]:
        if g["Invites"][str(i)]!="null":
            a.append(i)
            b += 1
        if b==9:
            break
    await leaderboard_embed(a,ctx.channel)

@client.command(pass_context=True)
async def server(ctx, id):
    if int(id) in g["Guilds"]:
        await ctx.send(g["Invites"][id])
        await guild_embed(client.get_guild(int(id)),ctx.channel)
    else:
        await ctx.send("VC Surfer is not in that server")

@client.command(pass_context=True)
async def levelChannel(ctx):
    if ctx.channel.permissions_for(ctx.author).manage_channels or ctx.author.id in kunny:
        g["LevelChannel"][str(ctx.guild.id)] = ctx.channel.id
        await ctx.send(f'VC Level changes will now be posted in {ctx.channel.name}')
    else:
        await ctx.send("You need to have the **Manage Channels** permission to set the leveling channel")


@client.command(pass_context=True)
async def setInvite(ctx, invite:discord.Invite):
    try:
        g["Invites"][str(ctx.guild.id)] = str(invite)
        await ctx.send("**Invite Set**")
    except:
        await ctx.send("No invite or an invalid invite was sent")

@client.command(pass_context=True)
async def categorize(ctx, category):
    if ctx.channel.permissions_for(ctx.author).administrator or ctx.author.id in kunny:
        g["Categories"][str(ctx.guild.id)] = category.lower()
        await ctx.send(f'**Set Server Category:** {category.lower()}')
    else:
        await ctx.send("You must have **ADMINISTRATOR** permissions to set the server's category")

@client.command(pass_contect=True)
async def help(ctx):
    await help_embed(ctx.channel)

@client.command(pass_context=True)
async def info(ctx):
    await info_embed(ctx.channel)

@client.command(pass_context=True)
async def support(ctx):
    await ctx.send("https://discord.gg/teWBAjs")
    await ctx.send("Join this server and ping a staff member")

@client.command(pass_context=True)
async def get_servers(ctx):
    if ctx.author.id in kunny:
        try:
            await client.get_user(354386735414640650).dm_channel.send(f'{g["Servers"]}')
        except:
            await client.get_user(354386735414640650).create_dm()
            await client.get_user(354386735414640650).dm_channel.send(f'{g["Servers"]}')

@client.command(pass_context=True)
async def test_embed(ctx):
    await vc_embed(ctx.channel)

async def remove_serv(id):
    global g

    if g["Servers"]<100:
        try:
            await client.get_user(354386735414640650).dm_channel.send(f'Removed {id} {g["Invites"][str(id)]}')
        except:
            await client.get_user(354386735414640650).create_dm()
            await client.get_user(354386735414640650).dm_channel.send(f'Removed {id} {g["Invites"][str(id)]}')

    g["Servers"] -= 1
    g["Guilds"].remove(id)
    g["VoiceUsers"].pop(str(id))
    g["Invites"].pop(str(id))
    g["Activity"].pop(str(id))
    await commit()
    
    print(f'Removed {id}')

async def add_serv(id):
    global g
    g["Servers"] += 1
    g["Guilds"].append(id)
    g["VoiceUsers"][str(id)] = await vc_count(client.get_guild(id))
    g["XP"][str(id)] = 0
    g["Activity"][str(id)] = 0
    g["Level"][str(id)] = 1

    if g["Servers"]<100:
        try:
            await client.get_user(354386735414640650).dm_channel.send(f'Added {id}')
        except:
            await client.get_user(354386735414640650).create_dm()
            await client.get_user(354386735414640650).dm_channel.send(f'Added {id}')

    try:
        await client.get_guild(id).owner.create_dm()
        await vc_embed(client.get_guild(id).owner.dm_channel)
    except:
        pass

    await commit()

    try:
        g["Invites"][str(id)] = await make_invite(client.get_guild(id))
    except:
        g["Invites"][str(id)] = "null"

    try:
        text = await get_text(client.get_guild(id))
        await vc_embed(text)
    except:
        pass
    try:
        check.start()
    except:
        pass
    
    
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
    if g["VoiceUsers"][str(guild.id)]<=1:
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
    embed.add_field(name="v/surf [category]",value="```Find active vc. Category is optional```",inline=True)
    embed.add_field(name="v/leaderboard",value="```List of most active servers```",inline=True)
    embed.add_field(name="v/categorize <category>",value="```Categorize server```",inline=True)
    embed.add_field(name="v/help",value="```More commands```",inline=True)
    await text.send(embed=embed)

async def help_embed(text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name="VC Surfer",icon_url=client.user.avatar_url)
    embed.add_field(name="v/surf [category]",value="```Find servers with active vcs. Category is optional```",inline=True)
    embed.add_field(name="v/leaderboard",value="```Get list of most active servers```",inline=True)
    embed.add_field(name="v/server <Id>",value="```Get specific server by id```",inline=True)
    embed.add_field(name="v/setInvite <Invite>",value="```Set the invite that the bot sends```",inline=True)
    embed.add_field(name="v/levelChannel",value="```Set this channel for vc level ups```",inline=True)
    embed.add_field(name="v/activity",value="```Get server's current activity```",inline=True)
    embed.add_field(name="v/level",value="```Get server's current vc level```",inline=True)
    embed.add_field(name="v/categorize <category>",value="```Categorize server```",inline=True)
    embed.add_field(name="v/info",value="```Bot info```",inline=True)
    embed.add_field(name="v/support",value="```Get support if bot isn't working properly```",inline=True)
    await text.send(embed=embed)

async def guild_embed(guild, text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name=guild.name,icon_url=guild.icon_url)
    embed.add_field(name="Activity",value=f'```{g["Activity"][str(guild.id)]}```',inline=True)
    embed.add_field(name="Level",value=f'```{g["Level"][str(guild.id)]}```',inline=True)
    embed.add_field(name="Voice Users",value=f'```{g["VoiceUsers"][str(guild.id)]}```',inline=True)
    embed.add_field(name="Invite",value=f'```{g["Invites"][str(guild.id)]}```',inline=True)
    if str(guild.id) in g["Categories"].keys() and g["Categories"][str(guild.id)]!=None:
        embed.set_footer(text=f'Category: {g["Categories"][str(guild.id)]}')
    await text.send(embed=embed)

async def leaderboard_embed(guilds,text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name="Most Active Servers",icon_url=client.user.avatar_url)
    for i in guilds:
        embed.add_field(name=client.get_guild(i),value=f'```Invite:{g["Invites"][str(i)][-7:]}\nLevel:{g["Level"][str(i)]}\nActivity:{g["Activity"][str(i)]}```',inline=True)
    message = await text.send(embed=embed)

async def info_embed(text):
    embed = discord.Embed(title = None, 
        description=None, 
        colour=discord.Colour.blue()
    )
    embed.set_author(name="Created by Kunny#4578",icon_url="https://cdn.discordapp.com/avatars/354386735414640650/fd5d86593540efbece7be9e30e389115.png?size=256")
    await text.send(embed=embed)

async def commit():
    with open('guilds.json','w') as i:
        i.write(json.dumps(g, indent=1))
        i.close()

def active_sort(id):
    multi = 1
    if g["Invites"][str(id)]=="null":
        multi=0
    return g["Activity"][str(id)]*multi

client.run('TOKEN')
