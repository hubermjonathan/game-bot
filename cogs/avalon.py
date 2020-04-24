import globals
from enum import Enum
import random
import time
import discord
from discord.ext import commands


class Characters(Enum):
    MERLIN = 1
    ASSASSIN = 2
    GOOD_SERVANT = 3
    EVIL_SERVANT = 4


class Board:
    def __init__(self, number_of_players):
        self.leader = random.randint(0, number_of_players - 1)
        self.successes = 0
        self.fails = 0
        self.failed_votes = 0

        if number_of_players == 5:
            self.number_on_quest = [2, 3, 2, 3, 3]
            self.fails_needed = [1, 1, 1, 1, 1]
            self.number_of_good = 2
            self.number_of_evil = 1
        elif number_of_players == 6:
            self.number_on_quest = [2, 3, 4, 3, 4]
            self.fails_needed = [1, 1, 1, 1, 1]
            self.number_of_good = 3
            self.number_of_evil = 1
        elif number_of_players == 7:
            self.number_on_quest = [2, 3, 3, 4, 4]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 3
            self.number_of_evil = 2
        elif number_of_players == 8:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 4
            self.number_of_evil = 2
        elif number_of_players == 9:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 5
            self.number_of_evil = 2
        elif number_of_players == 10:
            self.number_on_quest = [3, 4, 4, 5, 5]
            self.fails_needed = [1, 1, 1, 2, 1]
            self.number_of_good = 5
            self.number_of_evil = 3

    def succeed_vote(self):
        self.failed_votes = 0

    def fail_vote(self):
        self.failed_votes += 1

    def succeed_quest(self):
        self.successes += 1

    def fail_quest(self):
        self.fails += 1

    def did_good_win(self):
        return self.successes >= 3

    def did_evil_win(self):
        return self.fails >= 3


class Player:
    def __init__(self, member):
        self.member = member
        self.character = None

    def set_character(self, character):
        self.character = character

    def is_merlin(self):
        return self.character == Characters.MERLIN

    def is_good(self):
        return self.character == Characters.MERLIN or self.character == Characters.GOOD_SERVANT

    def is_assassin(self):
        return self.character == Characters.ASSASSIN

    def is_bad(self):
        return self.character == Characters.ASSASSIN or self.character == Characters.EVIL_SERVANT


class Avalon(commands.Cog):
    # constructor
    def __init__(self, bot):
        self.bot = bot
        self.in_progress = False
        self.number_of_players = None
        self.board = None
        self.players = []
        self.round = 0

    # event:
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # cases to ignore the event
        if member.bot:
            return

        # add the friend of purdue role and change nickname
        await member.edit(nick='???\'s Friend', roles=[member.guild.get_role(globals.FRIEND_OF_PURDUE_ROLE)])

    # avalon command group
    @commands.group()
    async def avalon(self, ctx):
        pass

    # command: start a game of avalon
    @avalon.command()
    @commands.is_owner()
    async def start(self, ctx):
        # clear the channel
        messages = await ctx.channel.history().flatten()
        await ctx.channel.delete_messages(messages)

        # unwrap context
        message = ctx.message
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        voice_channel = None
        for vc in guild.voice_channels:
            if voice_channel is not None:
                break

            for m in vc.members:
                if m.id == author.id:
                    voice_channel = vc
                    break
        if voice_channel is None:
            return
        members = voice_channel.members
        self.number_of_players = len(members)

        # TESTING
        members = [author, author, author, author, author, author, author]
        self.number_of_players = len(members)

        # cases to ignore the command
        # if self.in_progress or self.number_of_players < 5 or self.number_of_players > 10:
        #     return

        # create the board
        self.in_progress = True
        self.board = Board(self.number_of_players)

        # assign characters to players
        self.players = []
        for m in members:
            self.players.append(Player(m))
        random.shuffle(self.players)
        self.players[0].set_character(Characters.MERLIN)
        self.players[1].set_character(Characters.ASSASSIN)
        bad_players_string = '**' + self.players[1].member.nick + '** (' + self.players[1].member.name + '), '
        for i in range(2, self.number_of_players):
            if i == self.number_of_players - 1:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += 'and **' + self.players[1].member.nick + '** (' + self.players[
                    1].member.name + ')'
            elif i >= 2 + self.board.number_of_good:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += '**' + self.players[1].member.nick + '** (' + self.players[1].member.name + '), '
            else:
                self.players[i].set_character(Characters.GOOD_SERVANT)

        # message each player
        for p in self.players:
            await p.member.send('------------------------------------------------------------------------------\n' +
                                'You are playing: **AVALON**\n\n' +
                                '**The objective:**\n' +
                                'If you are good, you must successfully complete three quests. If you are evil,'
                                'you win if three quests end in failure or if Merlin is assassinated.\n\n' +
                                '**The characters:**\n' +
                                'Merlin (Good) - Merlin knows who the evil players are, ' +
                                'but must remain hidden to avoid assassination\n' +
                                'Assassin (Evil) - Before the good players claim victory, ' +
                                'the Assassin gets to kill one player\n' +
                                'Good Servant (Good) - A mere minion just trying to '
                                'successfully complete three quests\n' +
                                'Evil Servant (Evil) - A mere minion just trying to '
                                'have three quests end in failure\n\n' +
                                '**Gameplay:**\n' +
                                'Each round has two phases: the teambuilding phase and the quest phase. ' +
                                'During the teambuilding phase, the Leader for the round proposes a team to go ' +
                                'on the quest. Players will vote to either approve or reject the team. ' +
                                'If the team is rejected, then the failed votes counter gets incremented ' +
                                'and the quest phase is skipped. If the team is approved, each player on the team ' +
                                'will either vote to succeed or fail the quest. Good players must vote to succeed, ' +
                                'but evil players can choose to either succeed or fail. The quest will fail if the ' +
                                'number of fails needed is met. After each round, the leader rotates to the ' +
                                'next player and it begins again\n' +
                                '------------------------------------------------------------------------------')
            await p.member.send('You are playing as **' + p.character.name + '** this round')
            if p.is_merlin():
                await p.member.send('The evil players this round are ' + bad_players_string)
            elif p.is_bad():
                await p.member.send('Your teammates this round are ' + bad_players_string)

        round_handler()

    # function: handles the game flow
    async def round_handler(self):
        while not self.board.did_good_win() and not self.board.did_evil_win():
            # start the round
            self.round += 1

            # wait for the leader to choose his team
            self.is_leader_choosing = True
            while self.is_leader_choosing:
                pass

            # wait for all players to vote
            self.are_players_voting = True
            while self.are_players_voting:
                pass

            # check if the team is