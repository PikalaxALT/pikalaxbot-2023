import discord
from . import is_bot_owner
from ..botclass import PikalaxBOT


async def setup(bot: PikalaxBOT):
    @discord.app_commands.check(is_bot_owner)
    @bot.tree.command()
    async def shutdown(interaction: discord.Interaction):
        """Shuts down the bot. After this action, the bot will stop responding to commands."""
        await interaction.response.send_message('Shutting down. Relaunch the python script to start back up.', ephemeral=True)
        await bot.close()
