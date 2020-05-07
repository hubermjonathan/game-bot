import random
import time
import discord
from discord.ext import commands
from .game import GameState, Characters, Player, Board


class Avalon(commands.Cog):
    # constructor
    def __init__(self, bot):
        # TODO: move all of this to the board
        self.bot = bot
        self.text_channel = None
        self.voice_channel = None
        self.game_state = GameState.NOT_PLAYING
        self.board = None
        self.round = 0
        self.players = []
        self.quest_players = []
        self.quest_votes = []
        self.vote_message = None

    # function: get player given member id
    def get_player(self, member):
        return discord.utils.find(lambda p: p.member.id == member, self.players)

    # function: get picture given character or success/fail
    @staticmethod
    def get_asset(name):
        if name == Characters.MERLIN:
            return discord.File('assets/MERLIN.jpg')
        elif name == Characters.ASSASSIN:
            return discord.File('assets/ASSASSIN.jpg')
        elif name == Characters.GOOD_SERVANT:
            return discord.File('assets/GOOD_SERVANT.jpg')
        elif name == Characters.EVIL_SERVANT:
            return discord.File('assets/EVIL_SERVANT.jpg')
        elif name == 'SUCCESS':
            return discord.File('assets/SUCCESS.jpg')
        elif name == 'FAIL':
            return discord.File('assets/FAIL.jpg')
        else:
            return None

    # function: handle the beginning of a round
    async def begin_round(self, quest):
        # update state
        self.round += quest
        self.board.select_next_leader()
        self.game_state = GameState.WAITING_FOR_LEADER

        # clear the channel and send game info
        messages_to_delete = await self.text_channel.history().flatten()
        await self.text_channel.delete_messages(messages_to_delete)
        await self.text_channel.send('**QUEST #' + str(self.round) + '**')
        await self.text_channel.send('There are currently **' + str(self.board.successes) +
                                     '** succeeded quests and **' + str(self.board.fails) + '** failed ones')
        await self.text_channel.send('**' + str(self.board.number_on_quest[self.round-1]) +
                                     '** people need to go on this quest, the counter is at **' +
                                     str(self.board.failed_votes) + '**')
        await self.text_channel.send('Who would you like to go on the quest ' +
                                     self.players[self.board.leader].member.mention + '?')

    # function: handle the end of a round
    async def end_round(self, quest):
        # check for win conditions
        if self.board.did_evil_win():
            await self.text_channel.send('The **EVIL** players have won!')
            await self.end_game()
            return
        elif self.board.did_good_win():
            await self.text_channel.send('The **GOOD** players have successfully passed ' +
                                         '3 quests! Assassin who would you like to kill?')
            self.game_state = GameState.WAITING_FOR_ASSASSIN
            return

        # clear out variables
        self.quest_players = []
        self.quest_votes = []
        self.vote_message = None
        await self.begin_round(quest)

    # function: handle the end of a game
    async def end_game(self):
        # reset all variables
        self.text_channel = None
        self.voice_channel = None
        self.game_state = GameState.NOT_PLAYING
        self.board = None
        self.round = 0
        self.players = []
        self.quest_players = []
        self.quest_votes = []
        self.vote_message = None

    # on message event: delete extra messages during the game
    @commands.Cog.listener()
    async def on_message(self, message):
        if self.text_channel is None:
            return
        if (message.channel.id == self.text_channel.id and
                self.game_state.value and
                not message.author.bot and
                'choose' not in message.content):
            await message.delete()

    # on reaction add event: handle voting
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # ignore all bot reactions
        if user.bot:
            return

        if self.game_state == GameState.WAITING_FOR_VOTE:
            # get emojis to reference
            approve_emoji = discord.utils.get(reaction.message.guild.emojis, name='approve')
            reject_emoji = discord.utils.get(reaction.message.guild.emojis, name='reject')

            # cases to accept the reaction
            is_correct_emoji = reaction.emoji == approve_emoji or reaction.emoji == reject_emoji
            is_correct_message = reaction.message.id == self.vote_message
            # TODO: figure out to make sure only 1 react is possible

            # process the reaction if its appropriate or remove it otherwise
            if is_correct_emoji and is_correct_message:
                # get reactions
                approve_reaction = discord.utils.get(reaction.message.reactions, emoji=approve_emoji)
                reject_reaction = discord.utils.get(reaction.message.reactions, emoji=reject_emoji)

                if approve_reaction.count + reject_reaction.count - 2 == len(self.players):
                    if approve_reaction.count > reject_reaction.count:
                        # team is approved, move to quest
                        self.board.succeed_vote()
                        await self.text_channel.send('The vote has **succeeded**, waiting on the quest...')
                        for p in self.quest_players:
                            if p.bot:
                                pass
                            elif self.get_player(p.id).is_good():
                                # send the good message
                                message = await p.send('You have been sent on the quest, ' +
                                                       'you must vote to pass since you are good')
                                await message.add_reaction('✅')
                            elif self.get_player(p.id).is_bad():
                                # send the bad message
                                message = await p.send('You have been sent on the quest, ' +
                                                       'you can either vote to pass or fail since you are bad')
                                await message.add_reaction('✅')
                                await message.add_reaction('❎')
                        self.game_state = GameState.WAITING_FOR_QUEST
                    else:
                        # team is rejected
                        self.board.fail_vote()
                        await self.text_channel.send('The vote has **failed**, the counter is at **' +
                                                     str(self.board.failed_votes) + '**')

                        # evil wins if 5 failed votes in a row
                        if self.board.failed_votes == 5:
                            await self.text_channel.send('The **EVIL** players have won!')
                            await self.end_game()
                            return

                        # finish the round
                        time.sleep(5)
                        await self.end_round(0)
            else:
                await reaction.remove(user)
        elif self.game_state == GameState.WAITING_FOR_QUEST:
            # cases to accept the reaction
            is_a_dm = reaction.message.guild is None
            is_on_quest = user in self.quest_players
            if self.get_player(user.id).is_good():
                is_correct_emoji = reaction.emoji == '✅'
            else:
                is_correct_emoji = reaction.emoji == '✅' or reaction.emoji == '❎'
            # TODO: figure out to make sure only 1 react is possible

            # process the reaction if its appropriate or remove it otherwise
            if is_a_dm and is_on_quest and is_correct_emoji:
                await user.send('Your vote has been processed, waiting for others to vote...')

                # add reaction to list
                if reaction.emoji == '✅':
                    self.quest_votes.append(1)
                elif reaction.emoji == '❎':
                    self.quest_votes.append(0)

                if len(self.quest_votes) == len(self.quest_players):
                    if self.quest_votes.count(0) >= self.board.fails_needed[self.round-1]:
                        # quest has failed
                        await self.text_channel.send(file=self.get_asset('FAIL'))
                        self.board.fail_quest()
                        pass
                    else:
                        # quest has succeeded
                        await self.text_channel.send(file=self.get_asset('SUCCESS'))
                        self.board.succeed_quest()
                        pass

                    # finish the round
                    time.sleep(5)
                    await self.end_round(1)
            else:
                await reaction.remove(user)

    # command: choose people
    @commands.command()
    async def choose(self, ctx):
        if self.game_state == GameState.WAITING_FOR_LEADER:
            # cases to accept the command
            is_leader = ctx.author.id == self.players[self.board.leader].member.id
            is_correct_amount = len(ctx.message.mentions)-1 == self.board.number_on_quest[self.round-1]
            # TODO: figure out how to validate that mentions are playing the game

            # process the command if it is valid, delete it otherwise
            if is_leader and is_correct_amount:
                # get the players chosen for the quest
                quest_players = ctx.message.mentions
                for p in quest_players:
                    if p.bot:
                        quest_players.remove(p)
                self.quest_players = quest_players

                # wait for players to vote
                vote_message = await self.text_channel.send('Please vote approve or reject')
                await vote_message.add_reaction(discord.utils.get(ctx.guild.emojis, name='approve'))
                await vote_message.add_reaction(discord.utils.get(ctx.guild.emojis, name='reject'))
                self.vote_message = vote_message.id
                self.game_state = GameState.WAITING_FOR_VOTE
            else:
                await ctx.message.delete()
        elif self.game_state == GameState.WAITING_FOR_ASSASSIN:
            # cases to accept the command
            is_assassin = self.get_player(ctx.author.id).is_assassin()
            is_correct_amount = len(ctx.message.mentions)-1 == 1
            # TODO: figure out how to validate that mention is playing the game

            # process the command if it is valid, delete it otherwise
            if is_assassin and is_correct_amount:
                # check if the assassin killed merlin
                killed_player = None
                for m in ctx.message.mentions:
                    if m.bot:
                        pass
                    killed_player = self.get_player(m.id)
                if killed_player.is_merlin():
                    await self.text_channel.send('The **EVIL** players have won!')
                    await self.end_game()
                else:
                    await self.text_channel.send('The **GOOD** players have won!')
                    await self.end_game()
            else:
                await ctx.message.delete()
        else:
            await ctx.message.delete()

    # command: start a game of avalon
    @commands.command()
    async def start(self, ctx):
        # reset all variables
        await self.end_game()

        # clear the channel
        messages = await ctx.channel.history().flatten()
        await ctx.channel.delete_messages(messages)

        # grab the channels and players
        self.text_channel = ctx.channel
        for vc in ctx.guild.voice_channels:
            if ctx.author in vc.members:
                self.voice_channel = vc
                break
        if self.voice_channel is None:
            return
        members = self.voice_channel.members

        # cases to ignore the command
        if self.game_state.value or len(members) < 5 or len(members) > 10:
            return

        # create the board and assign characters
        self.board = Board(len(members))
        for m in members:
            self.players.append(Player(m))
        random.shuffle(self.players)
        self.players[0].set_character(Characters.MERLIN)
        self.players[1].set_character(Characters.ASSASSIN)
        bad_players_string = '**' + self.players[1].member.name + '**, '
        for i in range(2, len(self.players)):
            if i == len(self.players)-1:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += 'and **' + self.players[1].member.name + '**'
            elif i >= 2 + self.board.number_of_good:
                self.players[i].set_character(Characters.EVIL_SERVANT)
                bad_players_string += '**' + self.players[1].member.name + '**, '
            else:
                self.players[i].set_character(Characters.GOOD_SERVANT)

        # message each player
        await self.text_channel.send('Game beginning...')
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
            await p.member.send(file=self.get_asset(p.character))
            if p.is_merlin():
                await p.member.send('The evil players this round are ' + bad_players_string)
            elif p.is_bad():
                await p.member.send('Your teammates this round are ' + bad_players_string)

        # start the game
        await self.begin_round(1)
