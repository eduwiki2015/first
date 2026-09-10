"""네이버 블로그 자동 발행 (Playwright).

주의:
- 자동 로그인/발행은 네이버 이용약관 및 어뷰징 정책에 저촉될 수 있고,
  과도하게 사용하면 계정이 보호조치(캡차, 2단계 인증)되거나 블로그가
  저품질로 분류될 위험이 있다. 회사 소유 계정에서, 하루 발행량을
  사람 수준(1~3건)으로 유지하며 사용할 것.
- 브라우저는 화면에 보이는 상태(headful)로 실행된다. 캡차나 2단계 인증이
  뜨면 사람이 직접 해결한 뒤 자동화가 이어서 진행된다.
- 네이버 에디터(스마트에디터 ONE) 구조가 바뀌면 셀렉터 수정이 필요할 수 있다.

이 모듈은 Streamlit을 실행한 그 PC에서 브라우저를 띄우므로,
각 직원이 자기 PC에서 앱을 실행하는 구성에 적합하다.
"""

import time

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

LOGIN_URL = "https://nid.naver.com/nidlogin.login"
WRITE_URL = "https://blog.naver.com/{blog_id}?Redirect=Write&"

LOGIN_WAIT_SECONDS = 180  # 캡차/2단계 인증을 사람이 해결할 시간


def publish_post(
    naver_id: str,
    naver_pw: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    publish: bool = True,
) -> str:
    """네이버 블로그에 글을 작성한다.

    publish=False 이면 발행 버튼 직전까지만 진행하고 브라우저를 열어둔 채
    사람이 최종 확인 후 직접 발행하도록 한다.
    반환값: 진행 결과 메시지.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="ko-KR")
        page = context.new_page()

        # 1) 로그인
        page.goto(LOGIN_URL)
        page.fill("#id", naver_id)
        page.fill("#pw", naver_pw)
        # 로그인 버튼은 네이버가 구조를 자주 바꾸므로 여러 방법을 순서대로 시도
        for selector in ("#log\\.login", "button[type='submit']", ".btn_login"):
            try:
                page.click(selector, timeout=4000)
                break
            except PWTimeout:
                continue
        else:
            page.press("#pw", "Enter")  # 버튼을 못 찾으면 엔터키로 제출

        # 캡차/2단계 인증이 뜨면 사용자가 직접 해결할 때까지 대기
        deadline = time.time() + LOGIN_WAIT_SECONDS
        logged_in = False
        while time.time() < deadline:
            if "nidlogin" not in page.url and "nid.naver.com" not in page.url:
                logged_in = True
                break
            time.sleep(2)
        if not logged_in:
            browser.close()
            return "로그인 실패: 시간 내에 로그인이 완료되지 않았습니다. (캡차/2단계 인증 확인)"

        # 2) 글쓰기 페이지 진입
        page.goto(WRITE_URL.format(blog_id=naver_id))
        page.wait_for_load_state("networkidle")

        # 스마트에디터는 mainFrame iframe 안에 있음
        frame = page.frame(name="mainFrame") or page.main_frame

        # 이전 작성 글 이어쓰기 팝업 닫기
        try:
            frame.click(".se-popup-button-cancel", timeout=5000)
        except PWTimeout:
            pass
        # 도움말 패널 닫기
        try:
            frame.click(".se-help-panel-close-button", timeout=3000)
        except PWTimeout:
            pass

        # 3) 제목 입력
        frame.click(".se-section-documentTitle", timeout=15000)
        frame.type(".se-section-documentTitle", title, delay=30)

        # 4) 본문 입력 (문단 단위 입력)
        frame.click(".se-section-text")
        for line in body.split("\n"):
            page.keyboard.insert_text(line)
            page.keyboard.press("Enter")

        # 5) 발행
        if not publish:
            # 브라우저를 열어둔 채 사람이 확인/발행하도록 대기
            page.wait_for_timeout(600_000)
            browser.close()
            return "초안 작성 완료: 브라우저에서 직접 확인 후 발행하세요."

        frame.click(".publish_btn__m9KHH, [class*='publish_btn']", timeout=10000)

        # 태그 입력
        if tags:
            try:
                tag_input = frame.locator("#tag-input, [class*='tag_input']").first
                for tag in tags[:10]:
                    tag_input.fill(tag)
                    page.keyboard.press("Enter")
            except Exception:
                pass  # 태그 입력 실패는 발행을 막지 않음

        # 발행 확인 버튼
        frame.click("[class*='confirm_btn'], .btn_publish", timeout=10000)
        page.wait_for_load_state("networkidle")
        url = page.url
        browser.close()
        return f"발행 완료: {url}"
