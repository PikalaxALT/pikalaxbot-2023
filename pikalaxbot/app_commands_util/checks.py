import discord
from discord.ext import commands


# Adapted for hybrid commands
async def is_bot_owner(interaction: discord.Interaction | commands.Context):
    if isinstance(interaction, commands.Context):
        return await interaction.bot.is_owner(interaction.author)
    else:
        return await interaction.client.is_owner(interaction.user)
