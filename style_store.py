"""말투/스타일 프로필 저장소.

클로드 프로젝트처럼, 기존에 작성한 블로그 글들을 프로필로 저장해두면
글 생성 시 말투와 형식을 학습 자료로 사용한다.
JSON 파일로 저장되므로 같은 서버를 쓰는 직원들끼리 공유된다.
"""

import json
import re
from datetime import datetime
from pathlib import Path

STYLES_DIR = Path(__file__).parent / "styles"


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^\w가-힣 -]", "", name).strip().replace(" ", "_")
    if not cleaned:
        raise ValueError("프로필 이름이 비어 있습니다.")
    return cleaned


def list_profiles() -> list[str]:
    if not STYLES_DIR.exists():
        return []
    return sorted(p.stem for p in STYLES_DIR.glob("*.json"))


def load_profile(name: str) -> dict:
    path = STYLES_DIR / f"{_safe_name(name)}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_profile(name: str, samples: list[str], description: str = "") -> None:
    """samples: 기존 블로그 글 원문 목록 (말투 학습용)."""
    STYLES_DIR.mkdir(exist_ok=True)
    path = STYLES_DIR / f"{_safe_name(name)}.json"
    data = {
        "name": name,
        "description": description,
        "samples": [s.strip() for s in samples if s.strip()],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_profile(name: str) -> None:
    path = STYLES_DIR / f"{_safe_name(name)}.json"
    path.unlink(missing_ok=True)
