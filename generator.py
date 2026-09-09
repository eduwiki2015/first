"""블로그 글 생성 (Claude 또는 Gemini API)."""

import re
from typing import Iterator

import anthropic
import requests

from seo_guide import NAVER_SEO_GUIDE, OUTPUT_FORMAT_GUIDE

MODEL = "claude-opus-5"
GEMINI_MODEL = "gemini-2.5-flash"  # 무료 사용량 제공 모델
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

BASE_SYSTEM = f"""당신은 네이버 블로그 전문 작가입니다.
사용자가 준 키워드와 희망 내용으로 네이버 검색 상위노출에 최적화된 블로그 글을 작성합니다.

{NAVER_SEO_GUIDE}

{OUTPUT_FORMAT_GUIDE}
""".strip()

STYLE_SYSTEM_TEMPLATE = """
## 말투·형식 참고 자료

아래는 이 블로그에 기존에 올렸던 글들입니다. 새 글을 쓸 때 아래 글들의
말투(어미, 이모티콘 사용 여부, 존댓말/반말, 문장 길이), 문단 구성 방식,
소제목 스타일, 글 여닫는 방식을 최대한 비슷하게 따라 하세요.
내용을 베끼지는 말고 스타일만 모방합니다.

{samples}
""".strip()


def _style_text(style_samples: list[str] | None) -> str | None:
    if not style_samples:
        return None
    joined = "\n\n".join(
        f"### 기존 글 {i + 1}\n{s}" for i, s in enumerate(style_samples)
    )
    return STYLE_SYSTEM_TEMPLATE.format(samples=joined)


def _build_system(style_samples: list[str] | None) -> list[dict] | str:
    style = _style_text(style_samples)
    if not style:
        return BASE_SYSTEM
    # 스타일 샘플은 요청마다 동일하므로 프롬프트 캐싱으로 비용 절감
    return [
        {"type": "text", "text": BASE_SYSTEM},
        {"type": "text", "text": style, "cache_control": {"type": "ephemeral"}},
    ]


def _build_user_prompt(keyword: str, brief: str, extra: str = "") -> str:
    parts = [
        f"핵심 키워드: {keyword}",
        f"글에 담고 싶은 내용:\n{brief}",
    ]
    if extra.strip():
        parts.append(f"추가 요청사항:\n{extra}")
    parts.append("위 조건으로 네이버 블로그 글을 작성해 주세요.")
    return "\n\n".join(parts)


def stream_post(
    keyword: str,
    brief: str,
    style_samples: list[str] | None = None,
    extra: str = "",
    api_key: str | None = None,
    provider: str = "claude",
) -> Iterator[str]:
    """글을 생성한다. 텍스트 조각을 순서대로 yield.

    provider: "claude" (품질 우수, 유료) 또는 "gemini" (무료 사용량 제공).
    """
    if provider == "gemini":
        yield _gemini_generate(keyword, brief, style_samples, extra, api_key)
        return

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=_build_system(style_samples),
        messages=[{"role": "user", "content": _build_user_prompt(keyword, brief, extra)}],
    ) as stream:
        yield from stream.text_stream
        final = stream.get_final_message()
        if final.stop_reason == "refusal":
            detail = final.stop_details.explanation if final.stop_details else ""
            raise RuntimeError(f"모델이 요청을 거절했습니다: {detail}")


def _gemini_generate(
    keyword: str,
    brief: str,
    style_samples: list[str] | None,
    extra: str,
    api_key: str | None,
) -> str:
    """Google Gemini API로 글 생성 (무료 사용량 제공, aistudio.google.com에서 키 발급)."""
    if not api_key:
        raise RuntimeError(
            "Gemini API 키가 필요합니다. aistudio.google.com 에서 무료로 발급받아 "
            "사이드바에 입력해 주세요."
        )
    system = BASE_SYSTEM
    style = _style_text(style_samples)
    if style:
        system = f"{system}\n\n{style}"

    resp = requests.post(
        GEMINI_URL.format(model=GEMINI_MODEL),
        params={"key": api_key},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": _build_user_prompt(keyword, brief, extra)}],
                }
            ],
            "generationConfig": {"maxOutputTokens": 8192},
        },
        timeout=300,
    )
    if resp.status_code == 429:
        raise RuntimeError(
            "Gemini 무료 사용량을 초과했습니다. 잠시 후(또는 내일) 다시 시도하거나 "
            "Claude로 전환해 주세요."
        )
    if resp.status_code != 200:
        detail = resp.json().get("error", {}).get("message", resp.text[:300])
        raise RuntimeError(f"Gemini API 오류 ({resp.status_code}): {detail}")

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Gemini 응답을 해석할 수 없습니다: {str(data)[:300]}")
    return "".join(p.get("text", "") for p in parts)


def parse_post(raw: str) -> dict:
    """[제목]/[본문]/[태그] 형식의 출력을 분리한다."""
    title_m = re.search(r"\[제목\]\s*\n(.+?)(?=\n\[본문\])", raw, re.S)
    body_m = re.search(r"\[본문\]\s*\n(.+?)(?=\n\[태그\])", raw, re.S)
    tags_m = re.search(r"\[태그\]\s*\n(.+)", raw, re.S)

    title = title_m.group(1).strip() if title_m else ""
    body = body_m.group(1).strip() if body_m else raw.strip()
    tags: list[str] = []
    if tags_m:
        tags = [t.strip().lstrip("#") for t in tags_m.group(1).split(",") if t.strip()]
    return {"title": title, "body": body, "tags": tags}
