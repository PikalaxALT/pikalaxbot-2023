import discord
import random
import re
import string
import aiopoke
from discord import app_commands
import traceback
from ..botclass import PikalaxBOT
    
class HangmanView(discord.ui.View):
    accepted = list(string.ascii_uppercase) + ['♀', '♂', '2']

    def __init__(self, solution: aiopoke.PokemonSpecies, *, timeout=180):
        super().__init__(timeout=timeout)
        self.solution = solution
        self.guess_history = []
        self.solution_name = discord.utils.get(solution.names, language__name='en').name
        self.solution_clean = re.sub('[^\w♀♂]', '', self.solution_name).replace('é', 'e').upper()
        self.revealed = ['_'] * len(self.solution_clean)
        self.lives = 8
    
    def make_state_embed(self, *, name='???', description='???', colour=discord.Colour.blurple()):
        return (discord.Embed(name='???', description='???', colour=colour)
                .add_field(name='Revealed', value=' '.join(self.revealed))
                .add_field(name='Guess History', value=', '.join(self.guess_history))
                .add_field(name='Lives remaining', value=str(self.lives)))

    def register_guess(self, letter: str):
        if letter in self.guess_history:
            return 'Already guessed!'
        if letter not in HangmanView.accepted:
            return f'Invalid character! Choose a letter, binary gender symbol, or the number 2.'
        self.guess_history.append(letter)
        if letter not in self.solution_clean:
            self.lives -= 1
            if self.lives == 0:
                self.stop()
        else:
            self.revealed = [letter if c == letter else '_' for c in self.solution_clean]
            if self.revealed == list(self.solution_clean):
                self.stop()
    
    async def set_done(self):
        self.clear_items()
        self.revealed = list(self.solution_clean)
        return (self.make_state_embed(
            name=self.solution_name, 
            description=await discord.utils.get(self.solution.flavor_text_entries, language__name='en').flavor_text
        ).set_image(await (await discord.utils.get(self.solution.varieties, is_default=True).pokemon.fetch()).sprites.front_default.read()))


class Guess(discord.ui.TextInput):
    def __init__(self):
        super().__init__(label='Guess a letter', min_length=1, max_length=1, required=True)

    async def callback(self, interaction: discord.Interaction):
        e = ((response := self.view.register_guess(self.value.upper())) 
             and discord.Embed(description=response, colour=discord.Colour.dark_red)
             .set_author(name=interaction.user.display_name, icon_url=interaction.user.display_icon))
        embeds = [self.view.make_state_embed()]
        if e:
            embeds.append(e)
        await interaction.edit_original_response(embeds=embeds, view=self.view)


async def setup(bot: PikalaxBOT):
    @bot.tree.command()
    async def hangman(interaction: discord.Interaction):
        """Play a game of Pokemon Hangman. The solution will be the name of a Pokemon species."""
        natdex = await bot.natdex
        solution = await random.choice(natdex.pokemon_entries).pokemon_species.fetch()
        view = HangmanView(solution, timeout=90).add_item(Guess())
        await interaction.response.send_message('Playing Hangman! Anyone can join in! Use the text field below to play!', view=view)
        if await view.wait():
            content = f'Time\'s up, you did not guess in time. The correct answer was: {view.solution_name}'
        elif view.lives == 0:
            content = f'Too bad! You failed to guess the Pokemon. The correct answer was: {view.solution_name}'
        else:
            content = f'Whew, the man was saved! The correct answer was: {view.solution_name}'
        embed = await view.set_done()
        await interaction.edit_original_response(view=view, content=content, embed=embed)
    
    @hangman.error
    async def hangman_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=error.__class__.__name__,
            description=str(error)
        )
        if interaction.response.is_done():
            await interaction.edit_original_response(content='An error has occurred and the game has been cancelled.', view=None, embed=embed)
        else:
            await interaction.response.send_message('An error has occurred and the game has been cancelled.', embed=embed)
        print(''.join(traceback.format_exception(error)))
