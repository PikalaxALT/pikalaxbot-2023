import discord
import traceback
from discord import app_commands
from .checks import is_bot_owner
from ..botclass import PikalaxBOT


async def setup(bot: PikalaxBOT):
    @app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def shutdown(interaction: discord.Interaction):
        """Shuts down the bot. After this action, the bot will stop responding to commands on all servers."""
        await interaction.response.send_message('Shutting down. Restart the bot manually.', ephemeral=True)
        await bot.close()
    
    @app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def reload(interaction: discord.Interaction, extension: str):
        """Reload an extension on-the-fly"""
        await bot.reload_extension(extension)
        await bot.sync_app_commands()
        await interaction.response.send_message(f'Reloaded extension {extension}', ephemeral=True)
    
    @reload.error
    async def reload_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        await interaction.response.send_message('Unable to reload extension', embed=discord.Embed(colour=discord.Colour.red(), title=error.__class__.__name__, description=str(error)))
        traceback.print_exception(error)
    
    @app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def avatar(interaction: discord.Interaction, image: discord.Attachment):
        """Change the bot's avatar (profile picture) globally."""
        await bot.user.edit(avatar=await image.read())
        await interaction.response.send_message('Updated avatar', ephemeral=True)
