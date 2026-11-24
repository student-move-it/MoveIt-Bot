import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from bot_commands.movement import register_movement_commands

load_dotenv()


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
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Hosted by host.cogitdev.net",
        )
    )
    print(f"성공적으로 로그인했습니다: {client.user}")