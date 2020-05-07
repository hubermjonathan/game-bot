import discord
from discord.ext import commands


class Connection(commands.Cog):
    # constructor
    def __init__(self, bot):
        self.bot = bot

    # on connect event: print when connected
    @commands.Cog.listener()
    async def on_connect(self):
        print('connected to discord')

    # on disconnect event: print when disconnected
    @commands.Cog.listener()
    async def on_disconnect(self):
        print('disconnected from discord')

    # on ready event: print when ready
    @commands.Cog.listener()
    async def on_ready(self):
        print('bot is ready')
