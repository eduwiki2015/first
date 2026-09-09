"""Claude API 기반 블로그 글 생성."""

import re
from typing import Iterator

import anthropic

from seo_guide import NAVER_SEO_GUIDE, OUTPUT_FORMAT_GUIDE

MODEL = "claude-opus-5"

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


def _build_system(style_samples: list[str] | None) -> list[dict] | str:
    if not style_samples:
        return BASE_SYSTEM
    joined = "\n\n".join(
        f"### 기존 글 {i + 1}\n{s}" for i, s in enumerate(style_samples)
    )
    # 스타일 샘플은 요청마다 동일하므로 프롬프트 캐싱으로 비용 절감
    return [
        {"type": "text", "text": BASE_SYSTEM},
        {
            "type": "text",
            "text": STYLE_SYSTEM_TEMPLATE.format(samples=joined),
            "cache_control": {"type": "ephemeral"},
        },
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
) -> Iterator[str]:
    """글을 스트리밍으로 생성한다. 텍스트 조각을 순서대로 yield."""
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
