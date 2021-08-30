import os
from typing import List

import discord
from discord import member
from discord import role
from discord import emoji
from discord.ext import commands
from dotenv import load_dotenv

import random

import datetime

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
    def __init__(self, name, members: List[str], group):
        self.name = name
        self.dates = []
        self.daysHorizon = 21
        self.members = members
        self.group = group
        self.now = datetime.datetime.now()
        for day in range(0, self.daysHorizon):
            date = self.now + datetime.timedelta(days=day)
            self.dates.append(ScheduleDate(date, members))

class ScheduleDate:
    def __init__(self, date: datetime, expectedRespondants: List[str]):
        self.date = date
        self.expectedRespondants = expectedRespondants
        self.respondants = []
    
    def getMissingRespondants(self):
        return list(set(self.expectedRespondants) - set(self.respondants))

@bot.command()
async def schedule(ctx, name, command, group: role):
    if ctx.author == bot.user:
        return
    if command == "missing":
        #checks who is missing
        schedule = getCurrentSchedule(name, schedules)
        missing = set()
        for dates in schedule.dates:
            for date in dates:
                missingRespondants = date.getMissingRespondants()
                for missingRespondant in missingRespondants:
                    missing.add(missingRespondant)
        msg = "Event {}: The following people have not yet responded: ".format(name)
        for people in missing:
            msg += "{}, ".format(people)
        await ctx.send(msg)
        
    elif command == "extend":
        #adds another week of dates to the schedule
        schedule = getCurrentSchedule(name, schedules)
        newDates = []
        for newDate in range(schedule.daysHorizon, schedule.daysHorizon + 7):
            date = schedule.now + datetime.timedelta(days=newDate)
            newScheduleDate = ScheduleDate()
            newDates.append(newScheduleDate)
            schedule.dates.append(newScheduleDate)
        schedule.daysHorizon += 7
        await printNewDates(name, newDates, ctx, schedule)
                        
    else:
        #starts new schedule
        members = group.members
        schedules.append(ScheduleTask(name, members, group.mention))
        ctx.send("Event {}: Starting up new event. Dates in the next three weeks are listed below. React with :white_check_mark: if you can make a date and :negative_squared_cross_mark: if you are unavailable. You can alter your choices later. Summoning {}"
        .format(name, group.mention))
        schedule = getCurrentSchedule(name, schedules)
        await printNewDates(name, schedule.dates, ctx, schedule)

def getCurrentSchedule(name, schedules) -> ScheduleTask:
    return next(x for x in schedules if x.name == name)

async def printNewDates(name, newDates, ctx, schedule):
    await ctx.send("Event {}: Adding new dates. Please respond {}".format(name, schedule.group))
    emojis = [":white_check_mark:", ":negative_squared_cross_mark:"]
    for newDate in newDates:
        msg = await ctx.send("Event {}: {}".format(name, newDate.date))
        for emoji in emojis:
            await msg.add_reaction(emoji)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    

bot.run(TOKEN)