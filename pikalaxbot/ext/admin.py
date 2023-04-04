import discord
from discord import app_commands
from .checks import is_bot_owner
from ..botclass import PikalaxBOT


async def setup(bot: PikalaxBOT):
    @app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def shutdown(interaction: discord.Interaction):
        """Shuts down the bot. After this action, the bot will stop responding to commands on all servers."""
        await interaction.response.send_message('Shutting down. Relaunch the python script to start back up.', ephemeral=True)
        await bot.close()
    
    @app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def avatar(interaction: discord.Interaction, image: discord.Attachment):
        """Change the bot's avatar (profile picture) globally."""
        await bot.user.edit(avatar=await image.read())
        await interaction.response.send_message('Avatar updated', ephemeral=True)
