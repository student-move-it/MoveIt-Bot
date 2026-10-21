import os

import discord
from discord import app_commands

from bot_commands.movement import register_movement_commands


class MyClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        register_movement_commands(self.tree)

    async def setup_hook(self) -> None:
        await self.tree.sync()


client = MyClient()


@client.event
async def on_ready() -> None:
    print(f"성공적으로 로그인했습니다: {client.user}")


if __name__ == "__main__":
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if not bot_token:
        raise SystemExit("DISCORD_BOT_TOKEN 환경변수를 설정한 뒤 실행해 주세요.")
    client.run(bot_token)
