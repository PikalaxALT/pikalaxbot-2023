import discord
import random
import re
import aiopoke
from discord import app_commands
import traceback
from ..botclass import PikalaxBOT
    
class AnagramView(discord.ui.View):
    accepted = re.compile('[^A-Za-z2♀♂]+')

    def __init__(self, interaction: discord.Interaction, solution: aiopoke.PokemonSpecies, *, timeout=180):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.solution = solution
        self.guess_history = []
        self.solution_name = discord.utils.get(solution.names, language__name='en').name
        self.solution_clean = self.accepted.sub('', self.solution_name).replace('é', 'e').upper()
        while (revealed := ''.join(random.sample(self.solution_clean, len(self.solution_clean)))) == self.solution_clean:
            pass
        self.revealed = revealed
        self.lives = 8
        self.failed = None

    @discord.ui.button(style=discord.ButtonStyle.primary, label='Make a guess', emoji='❓')
    async def guess_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GuessModal(self))

    @discord.ui.button(style=discord.ButtonStyle.danger, label='Terminate the game', emoji='🛑')
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.permissions.manage_messages:
            await interaction.response.defer()
            self.stop(failed=None)
        else:
            await interaction.response.send_message('You do not have enough badges to cancel this game', ephemeral=True)

    def make_state_embed(self, *, name='???', description='???', colour=discord.Colour.blurple()):
        return (discord.Embed(title=name, description=description, colour=colour)
                .add_field(name='Revealed', value='`' + ' '.join(self.revealed) + '`')
                .add_field(name='Guess History', value=', '.join(self.guess_history))
                .add_field(name='Lives remaining', value=str(self.lives)))

    def register_guess(self, guess: str):
        self.guess_history.append(guess)
        if guess == self.solution_clean:
            return self.stop(failed=False)
        self.lives -= 1
        if self.lives == 0:
            self.stop(failed=True)
    
    def stop(self, *, failed: bool | None):
        self.failed = failed
        super().stop()
    
    async def set_done(self):
        self.clear_items()
        self.revealed = self.solution_clean
        return (self.make_state_embed(
            name=self.solution_name, 
            description=random.choice([x for x in self.solution.flavor_text_entries if x.language.name == 'en']).flavor_text,
            colour=discord.Colour.green() if self.failed is False else discord.Colour.red()
        ).set_image(url=(await discord.utils.get(self.solution.varieties, is_default=True).pokemon.fetch()).sprites.front_default.url))


class GuessModal(discord.ui.Modal):
    def __init__(self, top_view: AnagramView):
        super().__init__(title='Make your guess')
        self.top_view = top_view
        self.add_item(discord.ui.TextInput(label='Enter letter', min_length=len(top_view.solution_clean), max_length=len(top_view.solution_clean), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guess = self.children[0].value.upper()
        if guess in self.top_view.guess_history:
            message = 'This letter has already been guessed, try again.'
        elif self.top_view.accepted.search(guess):
            message = 'This is not a valid guess, try again.'
        else:
            self.top_view.register_guess(guess)
            return await self.top_view.interaction.edit_original_response(view=self.top_view, embed=self.top_view.make_state_embed())
        await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: PikalaxBOT):
    @bot.tree.command()
    async def anagram(interaction: discord.Interaction):
        """Play a game of Pokemon Anagram. The solution will be the name of a Pokemon species."""
        natdex = await bot.natdex
        solution = await random.choice(natdex.pokemon_entries).pokemon_species.fetch()
        view = AnagramView(interaction, solution)
        await interaction.response.send_message('Playing Anagram! Anyone can join in! Use the text field below to play!', view=view, embed=view.make_state_embed())
        if await view.wait():
            content = f'Time\'s up, you did not guess in time. The correct answer was: {view.solution_name}'
        elif view.failed is True:
            content = f'Too bad! You failed to guess the Pokemon. The correct answer was: {view.solution_name}'
        elif view.failed is False:
            content = f'Yes, you got the correct answer: {view.solution_name}'
        else:
            content = 'The game was cancelled'
        embed = await view.set_done()
        await interaction.edit_original_response(view=None, content=content, embed=embed)
    
    @anagram.error
    async def anagram_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        error = getattr(error, 'original', error)
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
