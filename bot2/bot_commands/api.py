import asyncio
import os
import re

import aiohttp


BASE_URL = os.getenv("MOVEMENT_API_BASE_URL", "https://move-it-be.vercel.app").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 15


async def create_movement(
    *,
    students: list[dict[str, str]],
    period_string: str,
    place: str,
    guild_id: int | None,
) -> str:
    payload = {
        "students": students,
        "periodString": period_string,
        "place": place,
    }
    params = {"guildId": str(guild_id)} if guild_id is not None else None
    api_key = os.getenv("API_KEY")
    if not api_key:
        return "API 요청 실패: 봇 실행 환경변수 API_KEY가 설정되지 않았습니다."
    headers = {"X-API-Key": api_key}

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    url = f"{BASE_URL}/move"
    print(f"[API 요청] POST {url} params={params!r} payload={payload!r}", flush=True)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json=payload,
                params=params,
                headers=headers,
            ) as response:
                try:
                    data = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    data = {}
                print(
                    f"[API 응답] POST {url} status={response.status} body={data!r}",
                    flush=True,
                )

                if response.status == 201:
                    period_numbers = re.findall(r"\d+", period_string)
                    if not period_numbers:
                        return data.get("message", "이동 현황이 등록되었습니다.")
                    start_period = period_numbers[0]
                    end_period = period_numbers[1] if len(period_numbers) > 1 else start_period
                    period_label = (
                        f"{start_period}교시"
                        if start_period == end_period
                        else f"{start_period}-{end_period}교시"
                    )
                    student_names = "\n".join(
                        f"학번이름: {student['studentNumber']} {student['name']}"
                        for student in students
                    )
                    return f"이동 등록 완료\n{student_names}\n시간: {period_label}\n장소: {place}"

                error = data.get("error", {})
                if isinstance(error, dict) and error.get("message"):
                    return f"이동 등록 실패: {error['message']}"
                if data.get("detail"):
                    return f"이동 등록 실패: {data['detail']}"
                if response.status == 409:
                    return "이동 등록 실패: 해당 교시에 이미 이동 등록된 학생이 있습니다."
                if response.status == 400:
                    return "이동 등록 실패: 학생 정보, 교시, 이동 장소를 올바르게 입력해 주세요."
                return f"이동 등록에 실패했습니다. (HTTP {response.status})"
    except asyncio.TimeoutError:
        print(f"[API 시간 초과] POST {url}", flush=True)
        return "이동 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
    except aiohttp.ClientError:
        print(f"[API 연결 오류] POST {url}", flush=True)
        return "이동 서버에 연결할 수 없습니다. 서버 주소와 네트워크를 확인해 주세요."


async def request_api(method: str, path: str, *, guild_id: int | None = None,
                      params: dict | None = None, payload: dict | None = None) -> str:
    key_env = "ADMIN_API_KEY" if method.upper() == "PUT" and path == "/classroom" else "API_KEY"
    api_key = os.getenv(key_env)
    if not api_key:
        return f"API 요청 실패: 봇 실행 환경변수 {key_env}가 설정되지 않았습니다."
    headers = {"X-API-Key": api_key}
    query = dict(params or {})
    if guild_id is not None:
        query["guildId"] = str(guild_id)
    query_items = [
        (key, value)
        for key, values in query.items()
        for value in (values if isinstance(values, (list, tuple)) else [values])
    ]
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    url = f"{BASE_URL}{path}"
    print(
        f"[API 요청] {method.upper()} {url} params={query_items!r} payload={payload!r}",
        flush=True,
    )
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, params=query_items or None,
                                       json=payload, headers=headers) as response:
                try:
                    data = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    data = {}
                print(
                    f"[API 응답] {method.upper()} {url} status={response.status} body={data!r}",
                    flush=True,
                )
                if response.status < 300:
                    if method.upper() == "PATCH" and path == "/analog-count" and payload is not None:
                        return f"{payload['change']:+d}명의 이동인원이 변경되었습니다"
                    return data.get("message", "요청이 처리되었습니다.")
                error = data.get("error", {})
                if isinstance(error, dict) and error.get("message"):
                    return f"요청 실패: {error['message']}"
                if data.get("detail"):
                    return f"요청 실패 (HTTP {response.status}): {data['detail']}"
                return f"요청 실패 (HTTP {response.status})"
    except asyncio.TimeoutError:
        print(f"[API 시간 초과] {method.upper()} {url}", flush=True)
        return "이동 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
    except aiohttp.ClientError:
        print(f"[API 연결 오류] {method.upper()} {url}", flush=True)
        return "이동 서버에 연결할 수 없습니다. 서버 주소와 네트워크를 확인해 주세요."
