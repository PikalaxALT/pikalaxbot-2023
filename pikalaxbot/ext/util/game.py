import discord
import re
import aiopoke
import random
from collections.abc import Sequence


class GuessModal(discord.ui.Modal):
    def __init__(self, top_view: 'GameView'):
        super().__init__(title='Make your guess')
        self.top_view = top_view
        self.add_item(discord.ui.TextInput(label='Enter guess', min_length=top_view.min_length, max_length=top_view.max_length, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guess = self.children[0].value.upper()
        if guess in self.top_view.guess_history:
            message = 'This has already been guessed, try again.'
        elif len(guess) not in (1, len(self.top_view.solution_clean)) or self.top_view.accepted.search(guess):
            message = 'This is not a valid guess, try again.'
        else:
            self.top_view.register_guess(guess)
            return await self.top_view.interaction.edit_original_response(view=self.top_view, embed=self.top_view.make_state_embed())
        await interaction.response.send_message(message, ephemeral=True)


class GameView(discord.ui.View):
    accepted = re.compile('[^A-Za-z2♀♂]+')

    def __init__(self, interaction: discord.Interaction, solution: aiopoke.PokemonSpecies, *, timeout=180):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.solution = solution
        self.guess_history = []
        self.solution_name = discord.utils.get(solution.names, language__name='en').name
        self.solution_clean = self.accepted.sub('', self.solution_name).replace('é', 'e').upper()
        self.lives = 8
        self.failed = None
        self.revealed = ...  # set by subclass
        self.min_length = None
        self.max_length = None
    
    def _init_revealed(self) -> Sequence[str]:
        return NotImplemented
    
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
        return (discord.Embed(title=f'{self.__class__.__name__}: {name}', description=description, colour=colour)
                .add_field(name='Revealed', value='`' + ' '.join(self.revealed) + '`')
                .add_field(name='Guess History', value=', '.join(self.guess_history))
                .add_field(name='Lives remaining', value=str(self.lives)))

    def handle_guess(self, guess: str) -> bool:
        return NotImplemented

    def register_guess(self, guess: str):
        self.guess_history.append(guess)
        if self.handle_guess(guess):
            if all(c == d for c, d in zip(self.revealed, self.solution_clean)):
                self.stop(failed=False)
        else:
            self.lives -= 1
            if self.lives == 0:
                self.stop(failed=True)
    
    def stop(self, *, failed: bool | None):
        self.failed = failed
        super().stop()
    
    async def set_done(self):
        self.clear_items()
        self.revealed = list(self.solution_clean)
        return (self.make_state_embed(
            name=self.solution_name, 
            description=random.choice([x for x in self.solution.flavor_text_entries if x.language.name == 'en']).flavor_text,
            colour=discord.Colour.green() if self.failed is False else discord.Colour.red()
        ).set_image(url=(await discord.utils.get(self.solution.varieties, is_default=True).pokemon.fetch()).sprites.front_default.url))
