import os
from typing import List

import discord
from discord import Member
from discord import Role
from discord import emoji
from discord import message
from discord.ext import commands
from dotenv import load_dotenv

import random

import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix="$", intents=intents)

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
async def order66(ctx, *, member: Member):
    if ctx.author == bot.user or member == bot.user:
        return
    await ctx.send("{} I'm sorry sir, it's time for you to leave.".format(member.mention))
    await ctx.send("https://i.ytimg.com/vi/WQsAo_6UKRs/maxresdefault.jpg")
    await member.move_to(None)

schedules = []

class ScheduleTask:
    def __init__(self, name, members: List[str], group, creator):
        self.name = name
        self.dates = []
        self.daysHorizon = 2#1
        self.members = members
        self.group = group
        self.creator = creator
        self.now = datetime.datetime.now()
        for day in range(0, self.daysHorizon):
            date = self.now + datetime.timedelta(days=day + 1) 
            msg = "Event {}: {}".format(name, date.strftime("%A %d %B %Y"))
            self.dates.append(ScheduleDate(date, members, msg))

class ScheduleDate:
    def __init__(self, date: datetime, expectedRespondants: List[str], msg: str):
        self.date = date
        self.expectedRespondants = expectedRespondants
        self.respondants = []
        self.msg = msg
    
    def getMissingRespondants(self):
        return list(set(self.expectedRespondants) - set(self.respondants))

@bot.command()
async def schedule(ctx, name: str, command, group: Role = None):
    if ctx.author == bot.user:
        return
    if command == "missing":
        #checks who is missing
        schedule = getCurrentSchedule(name, schedules)
        missing = set()
        for date in schedule.dates:
            missingRespondants = date.getMissingRespondants()
            for missingRespondant in missingRespondants:
                missing.add(missingRespondant)
        if len(missing) == 0:
            msg = "Event {}: Everyone has responded."
        else:
            msg = "Event {}: The following people have not yet responded: ".format(name)
            for people in missing:
                msg += "{}, ".format(people)
        await ctx.send(msg)
        
    elif command == "extend":
        #adds another week of dates to the schedule
        schedule = getCurrentSchedule(name, schedules)
        newDates = []
        for newDate in range(schedule.daysHorizon, schedule.daysHorizon + 7):
            date = schedule.now + datetime.timedelta(days=newDate + 1)
            msg = "Event {}: {}".format(name, date.strftime("%A %d %B %Y"))
            newScheduleDate = ScheduleDate(date, schedule.members, msg)
            newDates.append(newScheduleDate)
            schedule.dates.append(newScheduleDate)
        schedule.daysHorizon += 7
        await printNewDates(name, newDates, ctx, schedule)
                        
    elif command == "new":
        #starts new schedule
        if group == None:
            return
        if ':' in name:
            return # no colons in names
        members = [x.mention for x in group.members]
        schedules.append(ScheduleTask(name, members, group.mention, ctx.author.mention))
        await ctx.send("Event {}: Starting up new event. Dates in the next three weeks are listed below. React with :white_check_mark: if you can make a date and :negative_squared_cross_mark: if you are unavailable. You can alter your choices later."
        .format(name))
        schedule = getCurrentSchedule(name, schedules)
        await printNewDates(name, schedule.dates, ctx, schedule)

def getCurrentSchedule(name, schedules) -> ScheduleTask:
    return next(x for x in schedules if x.name == name)

async def printNewDates(name, newDates, ctx, schedule):
    await ctx.send("Event {}: Adding new dates. Please respond {}".format(name, schedule.group))
    emojis = ['✅', '❎']
    for newDate in newDates:
        msg = await ctx.send(newDate.msg)
        for emoji in emojis:
            await msg.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(data):
    if data.member.bot:
        return
    channel = await bot.fetch_channel(data.channel_id)
    message = await channel.fetch_message(data.message_id)
    if message.author != bot.user:
        return
    name = next(iter(message.content.split(":"))).replace("Event ", "")
    schedule = getCurrentSchedule(name, schedules)
    if data.emoji == "tick":
        
    
    
    

bot.run(TOKEN)