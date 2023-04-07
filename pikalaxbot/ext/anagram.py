import discord
import random
import re
import aiopoke
from discord import app_commands
import traceback
from ..botclass import PikalaxBOT
from .util.game import GameView


class Anagram(GameView):
    accepted = re.compile('[^A-Za-z2♀♂]+')

    def __init__(self, interaction: discord.Interaction, solution: aiopoke.PokemonSpecies, *, timeout=180):
        super().__init__(interaction, solution, timeout=timeout)
        self.min_length = self.max_length = len(self.solution_clean)
    
    def _init_revealed(self) -> str:
        while (revealed := ''.join(random.sample(self.solution_clean, len(self.solution_clean)))) == self.solution_clean:
            pass
        return revealed

    def handle_guess(self, guess: str):
        if guess == self.solution_clean:
            self.revealed = list(guess)
            return True
        return False


async def setup(bot: PikalaxBOT):
    @bot.tree.command()
    async def anagram(interaction: discord.Interaction):
        """Play a game of Pokemon Anagram. The solution will be the name of a Pokemon species."""
        view = Anagram(interaction, await bot.random_pokemon())
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
