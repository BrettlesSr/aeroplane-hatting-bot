import os
from typing import List

import discord
from discord import member
from discord.ext import commands
from dotenv import load_dotenv

import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Online")
        
@bot.command()
async def team(ctx):    
    if ctx.author == bot.user:
        return

    primaryChannel = ctx.author.voice.channel
    secondaryChannelIds = [717085375964774444, 717133960152481854]
    secondaryChannelId = next(x for x in secondaryChannelIds if x != primaryChannel.id)
    secondaryChannel = bot.get_channel(secondaryChannelId)

    authorChannel = ctx.author.voice.channel
    players = authorChannel.members
    random.shuffle(players)
    redTeam = []
    blueTeam = []

    for i in range(0, len(players)):
        player = players[i]
        if (i < len(players) / 2):
            redTeam.append(player)
        else:
            blueTeam.append(player)
        
    for bluePlayer in blueTeam:
        await bluePlayer.move_to(secondaryChannel)

    await ctx.send('Red Team: {}'.format([x.nick for x in redTeam]))
    await ctx.send('Blue Team: {}'.format([x.nick for x in blueTeam]))
    await ctx.send('glhf')

@bot.command()
async def order66(ctx, *, member: member):
    if ctx.author == bot.user or member == bot.user:
        return
    await ctx.send("{} I'm sorry sir, it's time for you to leave.".format(member.mention))
    await ctx.send("https://i.ytimg.com/vi/WQsAo_6UKRs/maxresdefault.jpg")
    await member.move_to(None)

schedules = []

class ScheduleTask:
    def __init__(self, name, members: List[str]):
        self.name = name
        self.dates = []
        self.daysHorizon = 21
        self.members = members
        self.messages = []
        for day in range(0, self.daysHorizon):
            self.dates.append(day)

@bot.command()
async def schedule(ctx, name, command):
    if ctx.author == bot.user:
        return
    if command == "missing":
        schedule = getCurrentSchedule(name, schedules)
        #checks who is missing
    elif command == "extend":
        schedule = getCurrentSchedule(name, schedules)
        #adds another week of dates to the schedule
    elif command == "close":
        schedule = getCurrentSchedule(name, schedules)
        #deletes all of the existing messages
    else:
        #starts new schedule
        members = []
        schedules.append(ScheduleTask(name, members))

def getCurrentSchedule(name, schedules) -> ScheduleTask:
    return next(x for x in schedules if x.name == name)

bot.run(TOKEN)