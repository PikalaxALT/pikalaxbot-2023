import discord
import dotenv
from .botclass import PikalaxBOT


async def command_prefix(bot: PikalaxBOT, message: discord.Message):
    return '-'  # TODO: implement database logic


def main():
    bot = PikalaxBOT(command_prefix, intents=discord.Intents.all())
    bot.run(dotenv.dotenv_values('.env')['DISCORD_PIKALAXBOT_TOKEN'])


if __name__ == '__main__':
    main()
