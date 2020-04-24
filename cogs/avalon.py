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
        self.number_of_players = number_of_players
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

    def select_next_leader(self):
        if self.leader == self.number_of_players-1:
            self.leader = 0
        else:
            self.leader += 1

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
        self.game_channel = None
        self.voice_channel = None
        self.in_progress = False
        self.number_of_players = None
        self.players = []
        self.board = None
        self.round = 0
        self.is_leader_choosing = False
        self.are_players_voting = False
        self.is_assassin_choosing = False

    # on reaction add event: handle voting on teams
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, member):
        pass

    # on message event: handle leader and assassin choosing
    @commands.Cog.listener()
    async def on_message(self, message):
        # cases to ignore the event
        if message.author.bot or discord.utils.get(message.mentions, bot=True) is not None:
            return

        # handle leader choosing team
        if self.is_leader_choosing:
            # cases to delete the message
            is_not_leader = message.author.id != self.players[self.board.leader].member.id
            is_not_correct_amount = len(message.mentions) != self.board.number_on_quest[self.round - 1]
            is_not_valid_players = False
            for p in self.players:
                if p not in m.mentions:
                    is_not_valid_players = True
            if is_not_leader or is_not_correct_amount or is_not_valid_players:
                await message.delete()
                return

            # continue the game
            self.is_leader_choosing = False

        # handle assassin killing someone
        if self.is_assassin_choosing:
            # cases to delete the message
            is_not_assassin = False
            is_not_correct_amount = len(message.mentions) != 1
            is_not_valid_players = False
            for p in self.players:
                if p not in m.mentions:
                    is_not_valid_players = True
            if is_not_assassin or is_not_correct_amount or is_not_valid_players:
                await message.delete()
                return

            # continue the game
            self.is_assassin_choosing = False

    # avalon command group
    @commands.group()
    async def avalon(self, ctx):
        pass

    # command: start a game of avalon
    @avalon.command()
    async def start(self, ctx):
        # clear the channel
        messages = await ctx.channel.history().flatten()
        await ctx.channel.delete_messages(messages)

        # unwrap context
        message = ctx.message
        self.game_channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        for vc in guild.voice_channels:
            if author in vc.members:
                self.voice_channel = vc
                break
        if self.voice_channel is None:
            return
        # TODO: REMOVE THIS
        # members = self.voice_channel.members
        # self.number_of_players = len(members)
        members = [author, author, author, author, author, author, author]
        self.number_of_players = len(members)

        # TODO: UNCOMMENT THIS
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
        bad_players_string = '**' + self.players[1].member.name + '**, '
        for i in range(2, self.number_of_players):
            if i == self.number_of_players - 1:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += 'and **' + self.players[1].member.name + '**'
            elif i >= 2 + self.board.number_of_good:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += '**' + self.players[1].member.name + '**, '
            else:
                self.players[i].set_character(Characters.GOOD_SERVANT)

        # message each player
        await self.game_channel.send('Assigning characters now...')
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

            # TODO: REMOVE THIS
            break

        await self.round_handler(ctx)

    # function: handles the overall game flow
    async def round_handler(self, ctx):
        while not self.board.did_good_win() and not self.board.did_evil_win():
            # start the round
            self.round += 1
            messages = await ctx.channel.history().flatten()
            await ctx.channel.delete_messages(messages)

            # send the game state
            await self.game_channel.send('Beginning round ' + str(self.round) + '...')
            await self.game_channel.send('There are currently **' + str(self.board.successes) +
                                         '** succeeded quests and **' + str(self.board.fails) + '** failed ones')

            # wait for the leader to choose his team
            await self.game_channel.send('Who would you like to go on the quest ' +
                                         self.players[self.board.leader].member.mention + '?')
            self.is_leader_choosing = True
            print('looping with ' + str(self.is_leader_choosing))
            while self.is_leader_choosing:
                pass

            # get the players chosen for the team
            messages = await self.game_channel.history().flatten()
            team_message = discord.utils.get(messages, id=self.game_channel.last_message_id)
            team_players = team_message.mentions

            # wait for all players to vote
            vote_message = await self.game_channel.send('Please vote approve or reject')
            await vote_message.add_reaction('\U0001F642')
            await vote_message.add_reaction('\U0001F643')
            self.are_players_voting = True
            while self.are_players_voting:
                pass

            # TODO: IMPLEMENT WAITING FOR VOTES WITH CORRECT REACTIONS

            # check if the team is approved
            approve_reaction = discord.utils.get(vote_message.reactions, name='\U0001F642')
            reject_reaction = discord.utils.get(vote_message.reactions, name='\U0001F643')
            if approve_reaction.count > reject_reaction.count:
                # team is approved, move to quest
                self.board.succeed_vote()
                await self.quest(team_players)
            else:
                # team is rejected
                self.board.fail_vote()
                self.board.select_next_leader()

                # evil wins if 5 failed votes in a row
                if self.board.failed_votes == 5:
                    while self.board.fails < 3:
                        self.board.fail_quest()

        # handle end game scenarios
        if self.board.did_evil_win():
            await self.game_channel.send('The **EVIL** players have won!')
        elif self.board.did_good_win():
            await self.game_channel.send('The **GOOD** players have successfully passed ' +
                                         '3 quests! Assassin who would you like to kill?')

            # wait for the assassin to kill someone
            self.is_assassin_choosing = True
            while self.is_assassin_choosing:
                pass

            # check if the assassin killed merlin
            messages = await self.game_channel.history().flatten()
            kill_message = discord.utils.get(messages, id=self.game_channel.last_message_id)
            killed_player = discord.utils.find(lambda p: p.member.id == kill_message.mentions[0], self.players)
            if killed_player.is_merlin():
                await self.game_channel.send('The **EVIL** players have won!')
            else:
                await self.game_channel.send('The **GOOD** players have won!')

    # function: handles the quest
    async def quest(self, players):
        pass
