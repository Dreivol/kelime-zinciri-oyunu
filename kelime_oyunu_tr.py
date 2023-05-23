import discord
from discord.ext import commands
from requests_html import HTMLSession
import logging
import asyncio

logger = logging.getLogger("my_bot")

# Create a Discord Intents object that enables all events to be received
intents = discord.Intents().all()

# Create a new Bot instance with command prefix "-" and intents
bot = commands.Bot(command_prefix="-", intents=intents)

used_words = set()
last_char = ''
game_channel_ids = set()
game_started = False
deta = HTMLSession()


@bot.event
async def on_ready():
    print('Bot Online')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='Music | -help'))
    print('Bot is connected to the following servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

@bot.event
async def on_message(message):
    global used_words, last_char, game_started, last_player

    if message.author == bot.user:
        return
    
    if message.content == 'start' and not game_started and message.channel.id in game_channel_ids:
        used_words.clear()
        last_char = ''
        game_started = True
        last_player = None
        await message.channel.send('Oyuna hoş geldiniz! Lütfen bir kelime yazın.')

    elif message.content == 'end' and game_started and message.channel.id in game_channel_ids:
        used_words.clear()
        last_char = ''
        game_started = False
        await message.channel.send('Oyun bitti! Teşekkürler.')

    elif game_started and len(message.content.split()) == 1 and message.channel.id in game_channel_ids:
        word = message.content.lower()

        if word in used_words:
            message_to_delete = await message.channel.send(f'{word.upper()} kelimesini daha önce kullanmıştık. Lütfen yeni bir kelime deneyin.')
            await asyncio.sleep(1)
            await message.delete(delay=1)
            await message_to_delete.delete()
            return

        if last_player == message.author:
            message_to_delete = await message.channel.send(f"{message.author.mention}, sıra sizde değil!")
            await asyncio.sleep(1)
            await message.delete(delay=1)
            await message_to_delete.delete()
            return

        if not last_char or word[0] == last_char:
            url = f'https://sozluk.gov.tr/gts?ara={word}'
            response = deta.get(url)

            if "error" in response.json():
                message_to_delete = await message.channel.send(f'{word.upper()} kelimesi geçersiz. Lütfen tekrar deneyin.')
                await asyncio.sleep(1)
                await message.delete(delay=1)
                await message_to_delete.delete()

            else:
                data = response.json()

                if not last_char:
                    await message.add_reaction("✅")
                elif word[0] == last_char:
                    await message.add_reaction("✅")
                else:
                    message_to_delete = await message.channel.send(f'{word} kelimesi yanlış! "{last_char.upper()}" harfiyle başlamalı. Lütfen tekrar deneyin.')
                    await asyncio.sleep(1)
                    await message.delete(delay=1)
                    await message_to_delete.delete()

                used_words.add(word)
                last_char = data[0]['madde'][-1]
                last_player = message.author

                if len(used_words) == 25:
                    game_started = False
                    winner = message.author.mention
                    await message.channel.send(f'25 kelime doğru cevaplandı! Tebrikler {winner}!')
        else:
            message_to_delete = await message.channel.send(f'{word.upper()} kelimesi "{last_char.upper()}" harfiyle başlamalı. Lütfen tekrar deneyin.')
            await asyncio.sleep(1)
            await message.delete(delay=1)
            await message_to_delete.delete()

    await bot.process_commands(message)

@bot.command(name="set", help="Kelime zinciri oyununun oynanacağı metin kanalını ayarlar, oyunu o metin kanalında aktif eder.")
async def set(ctx):
    global game_channel_ids
    if ctx.channel.id in game_channel_ids:
        await ctx.send(f"Oyun kanalı {ctx.channel.mention} olarak ayarlanmış!")
        # await ctx.send("Bu kanal zaten oyun kanalı olarak ayarlanmış")
    else:
        game_channel_ids.add(ctx.channel.id)
        await ctx.send(f"Oyun kanalı {ctx.channel.mention} olarak ayarlandı!")

@bot.command(name='setcancel', aliases=["sc"], help="Kelime zinciri oyununun oynanmak istenmediği metin kanalında oyunu deaktif eder.")
async def setcancel(ctx):
    global game_channel_ids
    if ctx.channel.id in game_channel_ids:
        game_channel_ids.remove(ctx.channel.id)
        await ctx.send(f"Kelime zinciri oyunu {ctx.channel.mention} kanalında deaktif edildi.")
    else:
        await ctx.send(f"{ctx.channel.mention} kanalında zaten aktif değil.")

bot.run("YOUR TOKEN")