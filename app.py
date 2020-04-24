import globals
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from cogs.connection import Connection
from cogs.avalon import Avalon

# initialize global and environment variables
globals.init()
load_dotenv()

# create the bot
bot = commands.Bot(command_prefix=commands.when_mentioned,
                   help_command=None,
                   owner_id=globals.OWNER_ID)

# add all the cogs
bot.add_cog(Connection(bot))
bot.add_cog(Avalon(bot))

# run the bot
bot.run(os.getenv('TOKEN'))
