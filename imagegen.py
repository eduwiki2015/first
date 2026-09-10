"""Gemini 이미지 생성 (무료 사용량 일부 포함).

키는 글 생성용 Gemini 키와 동일하게 aistudio.google.com 에서 발급.
"""

import base64
import time

import requests

# 이미지 생성 가능 모델 후보. 구글이 이름을 바꾸면 앞에서부터 순서대로 시도한다.
IMAGE_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "gemini-2.0-flash-preview-image-generation",
]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_image(prompt: str, api_key: str | None) -> bytes:
    """설명(prompt)으로 이미지를 만들어 PNG 바이트를 반환한다."""
    if not api_key:
        raise RuntimeError(
            "이미지 생성에는 Gemini API 키가 필요합니다. aistudio.google.com 에서 "
            "무료로 발급받아 입력해 주세요."
        )
    full_prompt = f"{prompt}. 고품질 사진 스타일, 글자·워터마크 없이."
    body_base = {"contents": [{"parts": [{"text": full_prompt}]}]}
    last_detail = "알 수 없는 오류"

    for model in IMAGE_MODELS:
        model_gone = False
        for modalities in (["IMAGE"], ["TEXT", "IMAGE"]):
            body = dict(body_base)
            body["generationConfig"] = {"responseModalities": modalities}
            # 503(서버 혼잡) 재시도
            resp = None
            for _ in range(3):
                resp = requests.post(
                    URL.format(model=model),
                    params={"key": api_key},
                    json=body,
                    timeout=120,
                )
                if resp.status_code != 503:
                    break
                time.sleep(5)

            if resp.status_code == 200:
                for part in (
                    resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                ):
                    inline = part.get("inlineData") or part.get("inline_data")
                    if inline and inline.get("data"):
                        return base64.b64decode(inline["data"])
                last_detail = "응답에 이미지 데이터가 없습니다."
                continue
            if resp.status_code == 429:
                raise RuntimeError(
                    "Gemini 무료 이미지 사용량을 초과했습니다. 잠시 후 다시 시도해 주세요."
                )
            if resp.status_code == 503:
                raise RuntimeError(
                    "지금 구글 무료 서버가 혼잡합니다. 1~2분 뒤 다시 시도해 주세요."
                )
            try:
                last_detail = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                last_detail = resp.text[:200]
            if resp.status_code == 404:  # 이 모델명은 사용 불가 → 다음 모델
                model_gone = True
                break
            # 400(모달리티 미지원 등)이면 다음 모달리티 조합으로 재시도
        if model_gone:
            continue

    raise RuntimeError(f"이미지 생성 실패: {last_detail}")
