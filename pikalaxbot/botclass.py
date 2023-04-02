import discord
from discord.ext import commands
import dotenv

class PikalaxBOT(commands.Bot):
    _init_extensions = {'pikalaxbot.ext.admin'}
    _init_guilds = map(lambda x: discord.Object(int(x)), dotenv.dotenv_values('.env')['DISCORD_PIKALAXBOT_GUILDS'].split(','))

    async def setup_hook(self) -> None:
        for ext in PikalaxBOT._init_extensions:
            await self.load_extension(ext)
        for guild in PikalaxBOT._init_guilds:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
