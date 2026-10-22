import unicodedata

import discord
from discord import app_commands

from bot_commands.api import create_movement, request_api


def _student_from_nickname(nickname: str) -> dict[str, str]:
    parts = nickname.strip().split("_", maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].strip():
        raise ValueError("학생 닉네임을 `학번_이름` 형식으로 설정해 주세요. (예: `1215_하채은`)")
    return {"studentNumber": parts[0], "name": parts[1].strip()}


def _students_from_mentions(
    interaction: discord.Interaction,
    selected: tuple[discord.Member | None, ...],
) -> list[dict[str, str]]:
    members = [member for member in selected if member is not None]
    if not members:
        return [_student_from_nickname(interaction.user.display_name)]
    students = []
    seen_numbers = set()
    for member in members:
        student = _student_from_nickname(member.display_name)
        if student["studentNumber"] not in seen_numbers:
            students.append(student)
            seen_numbers.add(student["studentNumber"])
    return students


def register_movement_commands(tree: app_commands.CommandTree) -> None:
    @tree.command(name="이동", description="교시와 장소를 지정해 학생 이동을 등록합니다.")
    @app_commands.describe(
        교시="이동할 교시 (예: 8~10교시)",
        장소="이동할 장소 (예: 세미나4-1실)",
        학생1="멘션할 학생 (최대 5명). 모두 비우면 본인입니다.",
        학생2="멘션할 학생",
        학생3="멘션할 학생",
        학생4="멘션할 학생",
        학생5="멘션할 학생",
    )
    async def move(
        interaction: discord.Interaction,
        교시: str,
        장소: str,
        학생1: discord.Member | None = None,
        학생2: discord.Member | None = None,
        학생3: discord.Member | None = None,
        학생4: discord.Member | None = None,
        학생5: discord.Member | None = None,
    ) -> None:
        교시 = 교시.strip()
        장소 = 장소.strip()
        if not 교시 or not 장소:
            await interaction.response.send_message(
                "교시와 이동 장소를 모두 입력해 주세요.", ephemeral=True
            )
            return

        try:
            student_data = _students_from_mentions(
                interaction, (학생1, 학생2, 학생3, 학생4, 학생5)
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False, thinking=True)
        try:
            result = await create_movement(
                students=student_data,
                period_string=교시,
                place=장소,
                guild_id=interaction.guild_id,
            )
        except Exception:
            await interaction.followup.send(
                "이동 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(result, ephemeral=False)

    @tree.command(name="복귀", description="이동 중인 학생의 복귀를 요청합니다.")
    @app_commands.describe(
        학생1="멘션할 학생 (최대 5명). 멘션을 하지 않을 시 본인이동",
        학생2="멘션할 학생",
        학생3="멘션할 학생",
        학생4="멘션할 학생",
        학생5="멘션할 학생",
    )
    async def return_to_class(
        interaction: discord.Interaction,
        학생1: discord.Member | None = None,
        학생2: discord.Member | None = None,
        학생3: discord.Member | None = None,
        학생4: discord.Member | None = None,
        학생5: discord.Member | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return
        try:
            students = _students_from_mentions(
                interaction, (학생1, 학생2, 학생3, 학생4, 학생5)
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        numbers = [student["studentNumber"] for student in students]
        await interaction.response.defer(thinking=True)
        result = await request_api(
            "DELETE", "/move", guild_id=interaction.guild_id,
            params={"studentNumber": numbers},
        )
        await interaction.followup.send(result)

    @tree.command(name="전원복귀", description="이동 중인 모든 학생을 복귀 처리합니다.")
    async def return_all_to_class(interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        result = await request_api("DELETE", "/moveAll", guild_id=interaction.guild_id)
        await interaction.followup.send(result)

    @tree.command(name="수정", description="등록된 이동 정보의 수정을 요청합니다.")
    @app_commands.describe(
        교시="변경할 교시 (예: 8~10, 9교시)",
        장소="변경할 이동 장소 (예: 세미나 4-1)",
        학생1="멘션할 학생 (최대 5명). 멘션을 하지 않을 시 본인이동",
        학생2="멘션할 학생",
        학생3="멘션할 학생",
        학생4="멘션할 학생",
        학생5="멘션할 학생",
    )
    async def edit_move(
        interaction: discord.Interaction,
        교시: str,
        장소: str,
        학생1: discord.Member | None = None,
        학생2: discord.Member | None = None,
        학생3: discord.Member | None = None,
        학생4: discord.Member | None = None,
        학생5: discord.Member | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return
        try:
            students = _students_from_mentions(
                interaction, (학생1, 학생2, 학생3, 학생4, 학생5)
            )
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        values = [student["studentNumber"] for student in students]
        교시 = unicodedata.normalize("NFKC", 교시).strip()
        장소 = 장소.strip()
        if not 교시 or not 장소:
            await interaction.response.send_message("교시와 이동 장소를 모두 입력해 주세요.", ephemeral=True)
            return
        query = {"studentNumber": values}
        await interaction.response.defer(thinking=True)
        result = await request_api(
            "PATCH", "/move", guild_id=interaction.guild_id,
            params=query,
            payload={"periodString": 교시, "place": 장소},
        )
        await interaction.followup.send(result)

    @tree.command(name="교실설정", description="학년반과 전체 학생 수를 설정합니다.")
    @app_commands.describe(학년반="예: 1-2는 1학년 2반", 총인원="교실 전체 인원")
    async def set_classroom(interaction: discord.Interaction, 학년반: str, 총인원: int) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return
        parts = unicodedata.normalize("NFKC", 학년반).strip().split("-")
        if len(parts) != 2 or any(
                part.strip() not in "123456789" or len(part.strip()) != 1
                for part in parts
        ):
            await interaction.response.send_message(
                "학년반을 `1-2` 형식으로 입력해 주세요. (학년·반은 각각 1~9)",
                ephemeral=True,
            )
            return

        class_number = int(parts[0].strip()) * 10 + int(parts[1].strip())

        await interaction.response.defer(thinking=True)
        result = await request_api(
            "PUT",
            "/classroom",
            payload={
                "guildId": str(interaction.guild_id),
                "classNumber": class_number,
                "totalStudents": 총인원,
            },
            guild_id=interaction.guild_id,
        )
        await interaction.followup.send(result)

    @tree.command(name="인원수정", description="아날로그 이동 학생 수를 늘리거나 줄입니다.")
    @app_commands.describe(학생수="변경할 학생 수 (예: 2는 추가, -2는 감소)")
    async def add_analog(interaction: discord.Interaction, 학생수: int) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        result = await request_api("PATCH", "/analog-count", guild_id=interaction.guild_id,
                                   payload={"change": 학생수})
        await interaction.followup.send(result)
