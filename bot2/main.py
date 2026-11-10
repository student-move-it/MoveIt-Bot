import os

import discord
from discord import app_commands

from bot_commands.movement import register_movement_commands


class MyClient(discord.Client):
    # 명령어 트리를 만들고 이동 관련 명령어를 등록합니다.
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        register_movement_commands(self.tree)

    # 시작할 때 등록된 명령어를 디스코드와 동기화합니다.
    async def setup_hook(self) -> None:
        await self.tree.sync()


client = MyClient()


# 로그인에 성공하면 실행 중인 봇 계정을 출력합니다.
@client.event
async def on_ready() -> None:
    print(f"성공적으로 로그인했습니다: {client.user}")


if __name__ == "__main__":
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if not bot_token:
        raise SystemExit("DISCORD_BOT_TOKEN 환경변수를 설정한 뒤 실행해 주세요.")
    client.run(bot_token)
