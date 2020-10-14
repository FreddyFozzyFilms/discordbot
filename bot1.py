import discord
import asyncio
import random
import requests
import math

from PIL import Image, ImageOps
from discord.ext import commands
from io import BytesIO

client = commands.Bot(command_prefix = '.')

@client.event
async def on_ready():
    print('bot is ready')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)} ms')

@client.command(aliases=['8ball']) # all strings in aliases invoke cammond
async def _8ball(ctx, *, question):
    responses = ['As I see it, yes.',
                'Ask again later.',
                'Better not tell you now.',
                'Cannot predict now.',
                'Concentrate and ask again.',
                "Don't count on it.",
                'It is certain.',
                'It is decidedly so.',
                "I don't see why not"]
    await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

@client.command()
async def clear(ctx, amount=0):
    if amount == 0:
        amount = None
    else:
        amount+=1
    await ctx.channel.purge(limit=amount)

"""@client.command()
async def kick(ctx, member : discord.Member, *, reason=None):
    await member.kick(reason=reason)"""

@client.command()
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason)

@client.command()
async def text(ctx):
    attachment = ctx.message.attachments[0]
    response = requests.get(attachment.url)
    await ctx.send(response.text.split("\n")[0])

@client.command()
async def ascii(ctx, channel='Grey'):
    if not ctx.message.attachments:
        await ctx.send('must attach image')

    attachment = ctx.message.attachments[0]
    response = requests.get(attachment.url)

    if 'image' in response.headers['content-type']:
        img = Image.open(BytesIO(response.content))

        # Create Black and white Image
        if channel == 'R':
            img = img.getchannel('R')
        elif channel == 'G':
            img = img.getchannel('G')
        elif channel == 'B':
            img = img.getchannel('B')
        elif channel == 'A':
            print('Alpha')
            img = img.getchannel('A')
        else:
            img = ImageOps.grayscale(img)
        width, height = img.size

        factor = int ( math.floor(width/29) )
        width = int (round(width / factor))
        height = int (round(height / factor))

        if width > 29:
            width = 29

        print([width, height])
        img = img.resize((width, height),resample=Image.BILINEAR)
        img.save("test2.png")

        width, height = img.size
        for i in range(height):
            line = []
            for j in range(width):
                pixel = img.getpixel((j, i))
                if pixel > 150:
                    pixel = " "*2 + "$" + " "*2
                elif pixel > 75:
                    pixel = " "*1 + "%" + " "*1
                else:
                    pixel = " "*2 + " , " + " "*2
                line.append(pixel)
            line = ''.join(line)
            await ctx.send(line)
    else:
        await ctx.send('must attach image')

client.run('*******token*******')
