import discord
from discord.ext import commands
import dotenv
import aiopoke
from asyncstdlib import functools as aiofunctools

class PikalaxBOT(commands.Bot):
    _init_extensions = {'pikalaxbot.ext.admin', 'pikalaxbot.ext.hangman'}
    _init_guilds = [discord.Object(int(x)) for x in dotenv.dotenv_values('.env')['DISCORD_PIKALAXBOT_GUILDS'].split(',')]

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        self.pokeapi = None
    
    @aiofunctools.cached_property
    async def natdex(self):
        if not self.pokeapi:
            return None
        return await self.pokeapi.get_pokedex('national')
    
    @aiofunctools.cached_property
    async def pokeapi_language(self):
        if not self.pokeapi:
            return None
        return await self.pokeapi.get_language('en')

    async def setup_hook(self):
        self.pokeapi = aiopoke.AiopokeClient()
        for ext in PikalaxBOT._init_extensions:
            await self.load_extension(ext)
        await self.sync_app_commands()
    
    async def sync_app_commands(self):
        for guild in PikalaxBOT._init_guilds:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        
    async def close(self):
        try:
            await super().close()
        finally:
            await self.pokeapi.close()
