import os
import time
from typing import List
from attr import s

import discord
from discord import Member
from discord import Message
from discord import Role
from discord.ext import commands
from dotenv import load_dotenv

import random

import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix="$", intents=intents)
dateFormat ="%A %d %B %Y"

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

class ScheduleTask:
    def __init__(self, name, group, msgs):
        self.name = name
        self.dates = []
        self.daysHorizon = 14
        if group != None:
            self.members = [x.mention for x in group.members]
            self.group = group
        self.now = datetime.datetime.now()

        if msgs != None:
            for msg in msgs:
                if len(msg.role_mentions) > 0:
                    self.group = msg.role_mentions[0]
                    self.members = [x.mention for x in self.group.members]
            for msg in msgs:
                if isDate(msg.content):
                    date = ScheduleDate(None, self.members, msg.content, name, msg.reactions)
                    self.dates.append(date)
        else:
            for day in range(0, self.daysHorizon):
                date = self.now + datetime.timedelta(days=day + 1) 
                dateString = date.strftime(dateFormat)
                if dateString.startswith('Saturday') or dateString.startswith('Sunday'):
                    msg = "Event {}: {}".format(name, dateString + ' (Afternoon)')
                    self.dates.append(ScheduleDate(date, self.members, msg, name, msg.reactions))
                    msg = "Event {}: {}".format(name, dateString + ' (Evening)')
                    self.dates.append(ScheduleDate(date, self.members, msg, name, msg.reactions))
                else:
                    msg = "Event {}: {}".format(name, dateString)
                    self.dates.append(ScheduleDate(date, self.members, msg, name, msg.reactions))
       
    
    async def getMissingRespondents(self):
        missing = set()
        for date in self.dates:
            missingRespondents = await date.getMissingRespondents()
            for missingRespondent in missingRespondents:
                missing.add(missingRespondent)
        return missing
        
class ScheduleDate:
    def __init__(self, date: datetime, expectedRespondents: list, msg: str, name: str, reactions):
        if date != None:
            self.date = date
        else:
            self.date = datetime.datetime.strptime(msg.replace('Event ' + name + ': ', '').replace(' (Afternoon)', '').replace(' (Evening)', ''), dateFormat)
        
        self.expectedRespondents = set(expectedRespondents)
        self.respondents = set([])
        self.approvingRespondents = set([])
        self.msg = msg
        self.name = name
        self.warmedUp = False

        if reactions != None:
            self.reactions = reactions

    async def warmup(self):
        if self.warmedUp:
            return
        for reaction in self.reactions:
                async for user in reaction.users():
                    if user != bot.user:
                        self.respondents.add(user.mention)
                        if reaction.emoji == '✅':
                            self.approvingRespondents.add(user.mention)
        self.warmedUp = True
    
    async def getMissingRespondents(self):
        if not self.warmedUp:
            await self.warmup()
        return list(set(self.expectedRespondents) - set(self.respondents))

@bot.command()
async def schedule(ctx, name: str, command = "", group: Role = None):
    if ctx.author == bot.user:
        return
    
    if name == "help":
        await ctx.send("Commands take the form \"$schedule [name of Schedule] [command] [@role mention]\"")
        await ctx.send("Possible [command]s:\r\n\"new\" : Makes a new Schedule linked to the people in the @role mention.\r\n\"extend\" : Adds another week to the named Schedule.\r\n\"missing\" : Pings the missing people in the named Schedule.")
    
    if command == "missing":
        #checks who is missing
        schedule = await getCurrentSchedule(name, ctx.channel, group)
        if schedule == None:
            return
        missing = await schedule.getMissingRespondents()
        if len(missing) == 0:
            msg = "Event {}: Everyone has responded."
        else:
            msg = "Event {}: The following people have not yet responded: ".format(name)
            for people in missing:
                msg += "{}, ".format(people)
        await ctx.send(msg)
        
    elif command == "extend":
        #adds another week of dates to the schedule
        schedule = await getCurrentSchedule(name, ctx.channel, group)
        if schedule == None:
            return
        newDates = []
        for newDate in range(schedule.daysHorizon, schedule.daysHorizon + 7):
            date = schedule.now + datetime.timedelta(days=newDate + 1)
            msg = "Event {}: {}".format(name, date.strftime(dateFormat))
            newScheduleDate = ScheduleDate(date, schedule.members, msg, name, None)
            newDates.append(newScheduleDate)
            schedule.dates.append(newScheduleDate)
        schedule.daysHorizon += 7
        await printNewDates(name, newDates, ctx, group)
                        
    elif command == "new":
        await ctx.send("Event {}: Starting up new event. Dates in the next three weeks are listed below. React with :white_check_mark: if you can make a date and :negative_squared_cross_mark: if you are unavailable. You can alter your choices later."
        .format(name))

        #starts new schedule
        if group == None:
            return
        if ':' in name:
            return # no colons in names
        if isDate(name):
            return # no dates in names
                
        schedule = await getCurrentSchedule(name, ctx.channel, group)
        if schedule == None:
            return

        newDates = []
        for newDate in range(0, schedule.daysHorizon):
            date = schedule.now + datetime.timedelta(days=newDate + 1)
            dateString = date.strftime(dateFormat)
            if dateString.startswith('Saturday') or dateString.startswith('Sunday'):
                msg = "Event {}: {}".format(name, dateString + ' (Afternoon)')
                newScheduleDate = ScheduleDate(date, schedule.members, msg, name, None)
                newDates.append(newScheduleDate)
                schedule.dates.append(newScheduleDate)
                msg = "Event {}: {}".format(name, dateString + ' (Evening)')
                newScheduleDate = ScheduleDate(date, schedule.members, msg, name, None)
                newDates.append(newScheduleDate)
                schedule.dates.append(newScheduleDate)
            else:
                msg = "Event {}: {}".format(name, dateString)
                newScheduleDate = ScheduleDate(date, schedule.members, msg, name, None)
                newDates.append(newScheduleDate)
                schedule.dates.append(newScheduleDate)
            
        await printNewDates(name, newDates, ctx, group)

    # elif command == "blame":
    #     schedule = await getCurrentSchedule(name, ctx.channel, group)
    #     if schedule == None:
    #         return
        
    #     schedule.getMissingRespondents()
    #     for date in schedule.dates

async def getCurrentSchedule(name, channel, group) -> ScheduleTask:
    messages = []
    async for message in channel.history(limit=200):
        if message.author == bot.user and message.content.startswith('Event ' + name):
            ##msg = await channel.fetch_message(message.id)
            messages.append(message)
    return ScheduleTask(name, group, messages)    

async def printNewDates(name, newDates, ctx, group):
    await ctx.send("Event {}: Adding new dates. Please respond {}".format(name, group.mention))
    emojis = ['✅', '❎']
    for newDate in newDates:
        msg = await ctx.send(newDate.msg)
        for emoji in emojis:
            await msg.add_reaction(emoji)

# @bot.event
# async def on_raw_reaction_add(data):
#     if data == None or data.member == None or data.member.bot:
#         return
#     channel = await bot.fetch_channel(data.channel_id)
#     message = await channel.fetch_message(data.message_id)
#     if message.author != bot.user:
#         return
#     name = next(iter(message.content.split(":"))).replace("Event ", "")
#     schedule = await getCurrentSchedule(name, channel, None)
#     if schedule == None:
#         return
#     date = next(x for x in schedule.dates if x.msg == message.content)
#     if data.member.mention in date.expectedRespondents:
#         if str(data.emoji) == '✅' or str(data.emoji) == '❎':
#             date.respondents.add(data.member.mention)
#             if str(data.emoji) == '✅':
#                 date.approvingRespondents.add(data.member.mention)
#     await checkIfCompleted(schedule, channel)

# @bot.event
# async def on_raw_reaction_remove(data):
#     user = await bot.fetch_user(data.user_id)
#     if data == None or user == None or user.bot:
#         return
#     channel = await bot.fetch_channel(data.channel_id)
#     message = await channel.fetch_message(data.message_id)
#     if message.author != bot.user:
#         return
#     name = next(iter(message.content.split(":"))).replace("Event ", "")
#     schedule = await getCurrentSchedule(name, channel, None)
#     if schedule == None:
#         return
#     date = next(x for x in schedule.dates if x.msg == message.content)
    
#     if user.mention in date.expectedRespondents:
#         if str(data.emoji) == '✅' or str(data.emoji) == '❎':
#             date.respondents.remove(user.mention)
#             if str(data.emoji) == '✅':
#                 date.approvingRespondents.remove(user.mention)
#     await checkIfCompleted(schedule, channel)
    
async def checkIfCompleted(schedule: ScheduleTask, channel):
    missing = await schedule.getMissingRespondents()
    if len(missing) == 0:
        for date in schedule.dates:
            await date.warmup()
            if set(date.expectedRespondents) == set(date.approvingRespondents):
                selectedDate = date
        if selectedDate == None:
            await channel.send("Everyone in {} has now voted on every date, but no consensus was reached. You should run the command \"$schedule {} extend X\" where X is the nubmer of new days you wish to add.".format(schedule.group, schedule.name))
        else:
            await channel.send("The date {} has been selected, {}.".format(selectedDate.msg.replace('Event ' + selectedDate.name + ': ', ''), schedule.group.mention))

def isDate(input: str) -> bool:
    return 'Monday ' in input or 'Tuesday ' in input or 'Wednesday ' in input or 'Thursday ' in input or 'Friday ' in input or 'Saturday ' in input or 'Sunday ' in input

bot.run(TOKEN)