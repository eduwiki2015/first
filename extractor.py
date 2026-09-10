"""링크(네이버 블로그/카페 글)에서 본문 원고를 자동 추출.

말투 학습용으로, 원고를 직접 붙여넣는 대신 공개 글의 링크만 넣으면
브라우저로 접속해 본문 텍스트를 읽어온다.

주의:
- 네이버 블로그 공개글은 대체로 가능하지만, 카페글은 회원/등급 전용인 경우가
  많아 실패할 수 있다. 실패 시 직접 붙여넣기로 안내한다.
- 자동 수집은 상대 서비스 정책에 저촉될 수 있으니 본인/회사 글이나 공개 글에만 사용.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# 본문이 담기는 영역 후보 (스마트에디터 ONE, 구버전, 카페 등)
CONTENT_SELECTORS = [
    ".se-main-container",
    "#postViewArea",
    ".post_ct",
    ".ArticleContentBox",
    "#content-area",
    "article",
]


def _read_container(scope) -> str:
    for sel in CONTENT_SELECTORS:
        try:
            el = scope.query_selector(sel)
        except Exception:
            el = None
        if el:
            text = (el.inner_text() or "").strip()
            if len(text) > 50:  # 너무 짧으면 잘못 잡은 것
                return text
    return ""


def extract_text_from_url(url: str) -> str:
    """URL에서 본문 텍스트를 추출한다. 실패 시 RuntimeError."""
    url = url.strip()
    if not url.startswith("http"):
        raise RuntimeError("올바른 링크(주소)를 입력해 주세요. (http로 시작)")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="ko-KR")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2500)  # 본문 로딩 대기

            text = ""
            # 네이버 블로그/카페는 본문이 iframe 안에 있는 경우가 많음
            for frame in page.frames:
                text = _read_container(frame)
                if text:
                    break
            if not text:  # 마지막 수단: 페이지 전체 텍스트
                body = page.query_selector("body")
                text = (body.inner_text() if body else "").strip()
        except PWTimeout:
            raise RuntimeError("페이지를 여는 데 시간이 너무 오래 걸립니다. 링크를 확인해 주세요.")
        finally:
            browser.close()

    if not text or len(text) < 50:
        raise RuntimeError(
            "본문을 읽지 못했습니다. 비공개 글이거나 회원 전용 글일 수 있어요. "
            "이 경우 원고를 직접 붙여넣어 주세요."
        )
    # 과도하게 긴 경우 앞부분만 (말투 학습에는 충분)
    return text[:4000]
