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

    def __init__(self, interaction: discord.Interaction, solution: aiopoke.PokemonSpecies, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(GuessButton())
        self.interaction = interaction
        self.solution = solution
        self.guess_history = []
        self.solution_name = discord.utils.get(solution.names, language__name='en').name
        self.solution_clean = re.sub('[^\w♀♂]', '', self.solution_name).replace('é', 'e').upper()
        self.revealed = ['_'] * len(self.solution_clean)
        self.lives = 8
    
    def make_state_embed(self, *, name='???', description='???', colour=discord.Colour.blurple()):
        return (discord.Embed(title=name, description=description, colour=colour)
                .add_field(name='Revealed', value='`' + ' '.join(self.revealed) + '`')
                .add_field(name='Guess History', value=', '.join(self.guess_history))
                .add_field(name='Lives remaining', value=str(self.lives)))

    def register_guess(self, letter: str):
        self.guess_history.append(letter)
        if len(letter) == 1:
            if letter in self.solution_clean:
                self.revealed = [c if c == letter or d != '_' else '_' for c, d in zip(self.solution_clean, self.revealed)]
                if self.revealed == list(self.solution_clean):
                    self.stop()
                    return
        elif letter == self.solution_clean:
            self.revealed = list(self.solution_clean)
            self.stop()
            return
        self.lives -= 1
        if self.lives == 0:
            self.stop()
    
    async def set_done(self):
        self.clear_items()
        self.revealed = list(self.solution_clean)
        return (self.make_state_embed(
            name=self.solution_name, 
            description=discord.utils.get(self.solution.flavor_text_entries, language__name='en').flavor_text
        ).set_image(url=(await discord.utils.get(self.solution.varieties, is_default=True).pokemon.fetch()).sprites.front_default.url))


class GuessModal(discord.ui.Modal):
    def __init__(self, top_view: HangmanView):
        super().__init__(title='Make your guess')
        self.top_view = top_view
        self.add_item(discord.ui.TextInput(label='Enter letter', min_length=1, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guess = self.children[0].value.upper()
        if guess in self.top_view.guess_history:
            message = 'This letter has already been guessed, try again.'
        elif len(guess) not in (1, len(self.top_view.solution_clean)) or any(c not in self.top_view.accepted for c in guess):
            message = 'This is not a valid guess, try again.'
        else:
            self.top_view.register_guess(guess)
            return await self.top_view.interaction.edit_original_response(view=self.top_view, embed=self.top_view.make_state_embed())
        await interaction.response.send_message(message, ephemeral=True)


class GuessButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label='Make a guess', emoji='❓')

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GuessModal(self.view))


async def setup(bot: PikalaxBOT):
    @bot.tree.command()
    async def hangman(interaction: discord.Interaction):
        """Play a game of Pokemon Hangman. The solution will be the name of a Pokemon species."""
        natdex = await bot.natdex
        solution = await random.choice(natdex.pokemon_entries).pokemon_species.fetch()
        view = HangmanView(interaction, solution)
        await interaction.response.send_message('Playing Hangman! Anyone can join in! Use the text field below to play!', view=view, embed=view.make_state_embed())
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
        traceback.print_exception(error)
