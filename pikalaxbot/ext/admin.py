import discord
import traceback
from discord import app_commands
from discord.ext import commands
from ..app_commands_util.checks import is_bot_owner
from ..botclass import PikalaxBOT


async def setup(bot: PikalaxBOT):
    @commands.check(is_bot_owner)
    @bot.hybrid_command()
    async def shutdown(interaction: discord.Interaction):
        """Shuts down the bot. After this action, the bot will stop responding to commands on all servers."""
        await interaction.response.send_message('Shutting down. Restart the bot manually.', ephemeral=True)
        await bot.close()
    
    @commands.check(is_bot_owner)
    @bot.hybrid_command()
    async def reload(interaction: discord.Interaction, extension: str):
        """Reload an extension on-the-fly"""
        extension = extension.lower()
        await bot.reload_extension(f'pikalaxbot.ext.{extension}')
        # await bot.sync_app_commands()
        await interaction.response.send_message(f'Reloaded extension `{extension}`', ephemeral=True)
    
    @app_commands.check(is_bot_owner)
    @reload.autocomplete('extension')
    async def reload_autocomplete(interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=ext.rsplit('.', 1)[-1], value=ext.rsplit('.', 1)[-1]) for ext in bot.extensions if ext.lower().startswith(current.lower())][:25]
    
    @reload.error
    async def reload_error(ctx: commands.Context, error: commands.CommandError):
        error = getattr(error, 'original', error)
        await ctx.send('Unable to reload extension', embed=discord.Embed(colour=discord.Colour.red(), title=error.__class__.__name__, description=str(error)))
        traceback.print_exception(error)
    
    @commands.check(is_bot_owner)
    @bot.hybrid_command()
    async def avatar(interaction: discord.Interaction, image: discord.Attachment):
        """Change the bot's avatar (profile picture) globally."""
        await bot.user.edit(avatar=await image.read())
        await interaction.response.send_message('Updated avatar', ephemeral=True)
    
    @commands.check(is_bot_owner)
    @bot.hybrid_command()
    async def sync(interaction:discord.Integration):
        """Syncs application commands between the bot and Discord"""
        await bot.sync_app_commands()
        await interaction.response.send_message('Synced application commands', ephemeral=True)
