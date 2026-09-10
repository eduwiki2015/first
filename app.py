"""네이버 블로그 자동화 — 직원 공용 웹앱 (Streamlit).

실행: streamlit run app.py
"""

import os

import streamlit as st

import generator
import style_store

st.set_page_config(page_title="네이버 블로그 자동화", page_icon="✍️", layout="wide")
st.title("✍️ 네이버 블로그 자동화")

# ---------------------------------------------------------------- 사이드바
with st.sidebar:
    st.header("설정")
    provider_label = st.radio(
        "AI 선택",
        ["Gemini (무료 사용 가능)", "Claude (품질 우수, 유료)"],
        help="Gemini: aistudio.google.com 에서 카드 등록 없이 무료 키 발급. "
        "Claude: console.anthropic.com 에서 충전식 유료 키 발급.",
    )
    provider = "gemini" if provider_label.startswith("Gemini") else "claude"
    if provider == "gemini":
        api_key = st.text_input(
            "Gemini API 키",
            type="password",
            value=os.environ.get("GEMINI_API_KEY", ""),
            help="aistudio.google.com → Get API key 에서 무료 발급",
        )
    else:
        api_key = st.text_input(
            "Anthropic API 키",
            type="password",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            help="서버에 ANTHROPIC_API_KEY 환경변수가 있으면 비워둬도 됩니다.",
        )

    profiles = style_store.list_profiles()
    profile_name = st.selectbox(
        "말투 프로필",
        options=["(사용 안 함)"] + profiles,
        help="'말투 학습' 탭에서 기존 블로그 글을 저장하면 여기서 선택할 수 있습니다.",
    )

    st.divider()
    st.caption(
        "⚠️ 자동 발행 기능은 네이버 이용약관에 저촉될 수 있으며 과도한 사용 시 "
        "계정 보호조치·저품질 위험이 있습니다. 회사 계정에서 하루 1~3건 수준으로만 "
        "사용하세요. 가장 안전한 방법은 '복사해서 직접 붙여넣기'입니다."
    )

tab_write, tab_image, tab_style, tab_publish = st.tabs(
    ["📝 글 생성", "🖼️ 이미지 생성", "🎨 말투 학습", "🚀 네이버 발행"]
)

# ---------------------------------------------------------------- 글 생성
with tab_write:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        content_label = st.radio("글 종류", ["블로그 글", "카페 글"], horizontal=True)
        content_type = "cafe" if content_label == "카페 글" else "blog"
    with c2:
        keyword = st.text_input("핵심 키워드 (상위노출 목표)", placeholder="예: 강남 맛집")
    with c3:
        target_chars = st.number_input(
            "목표 글자수 (한글 기준)",
            min_value=0,
            max_value=5000,
            value=0,
            step=100,
            help="0으로 두면 글 종류별 권장 분량으로 자동 작성합니다. (예: 2000)",
        )
    extra = st.text_input("추가 요청사항 (선택)", placeholder="예: 존댓말로, 이모티콘 없이")
    brief = st.text_area(
        "글에 담고 싶은 내용",
        height=180,
        placeholder="예: 지난 주말 방문한 OOO 식당 후기. 파스타가 맛있었고 주차가 편했음. 가격대와 웨이팅 정보 포함.",
    )

    if st.button("글 생성하기", type="primary", use_container_width=True):
        if not keyword.strip() or not brief.strip():
            st.error("핵심 키워드와 글 내용을 입력해 주세요.")
        else:
            samples = None
            if profile_name != "(사용 안 함)":
                samples = style_store.load_profile(profile_name)["samples"]
            try:
                ai_name = "Gemini" if provider == "gemini" else "Claude"
                with st.status(f"{ai_name}가 글을 작성하는 중...", expanded=True):
                    placeholder = st.empty()
                    chunks: list[str] = []
                    for chunk in generator.stream_post(
                        keyword=keyword,
                        brief=brief,
                        style_samples=samples,
                        extra=extra,
                        api_key=api_key or None,
                        provider=provider,
                        content_type=content_type,
                        target_chars=int(target_chars) or None,
                    ):
                        chunks.append(chunk)
                        placeholder.markdown("".join(chunks))
                st.session_state["post"] = generator.parse_post("".join(chunks))
                st.success("글 생성 완료! 아래에서 수정 후 발행 탭으로 이동하세요.")
            except Exception as e:
                st.error(f"생성 실패: {e}")

    if "post" in st.session_state:
        post = st.session_state["post"]
        st.divider()
        st.subheader("생성 결과 (수정 가능)")
        post["title"] = st.text_input("제목", value=post["title"])
        post["body"] = st.text_area("본문", value=post["body"], height=400)
        post["tags"] = [
            t.strip()
            for t in st.text_input("태그 (쉼표 구분)", value=", ".join(post["tags"])).split(",")
            if t.strip()
        ]
        st.caption(f"본문 글자 수(공백 제외): {len(post['body'].replace(' ', '').replace(chr(10), ''))}자")

        full_text = f"{post['title']}\n\n{post['body']}\n\n태그: {', '.join('#' + t for t in post['tags'])}"
        st.download_button("📄 텍스트 파일로 저장", full_text, file_name="blog_post.txt", use_container_width=True)

# ---------------------------------------------------------------- 이미지 생성
with tab_image:
    import re as _re

    st.markdown("이미지는 **Gemini**로 생성합니다. (무료 사용량 일부 포함)")
    default_img_key = api_key if provider == "gemini" else os.environ.get("GEMINI_API_KEY", "")
    img_key = st.text_input(
        "Gemini API 키 (이미지용)",
        type="password",
        value=default_img_key,
        help="글 생성용 Gemini 키와 동일합니다. Claude를 선택했다면 여기에 Gemini 키를 따로 입력하세요.",
    )

    # 생성한 글에 들어 있는 [이미지: 설명] 을 자동으로 추천
    suggestions = []
    if "post" in st.session_state:
        suggestions = _re.findall(r"\[이미지:\s*(.+?)\]", st.session_state["post"]["body"])
    if suggestions:
        pick = st.selectbox("생성한 글에서 찾은 이미지 설명 (선택해서 넣기)", ["(직접 입력)"] + suggestions)
    else:
        pick = "(직접 입력)"

    img_prompt = st.text_input(
        "만들 이미지 설명",
        value="" if pick == "(직접 입력)" else pick,
        placeholder="예: 파스타가 담긴 접시, 아늑한 레스토랑 분위기, 밝은 조명",
    )

    if st.button("이미지 생성하기", type="primary", use_container_width=True):
        if not img_prompt.strip():
            st.error("이미지 설명을 입력해 주세요.")
        else:
            import imagegen

            try:
                with st.spinner("이미지를 만드는 중... (10~30초)"):
                    img_bytes = imagegen.generate_image(img_prompt, img_key or None)
                st.image(img_bytes, caption=img_prompt)
                st.download_button(
                    "🖼️ 이미지 저장 (PNG)",
                    img_bytes,
                    file_name="image.png",
                    mime="image/png",
                    use_container_width=True,
                )
                st.caption("저장한 이미지를 네이버 에디터에서 직접 첨부하시면 됩니다.")
            except Exception as e:
                st.error(f"이미지 생성 실패: {e}")

# ---------------------------------------------------------------- 말투 학습
with tab_style:
    st.markdown(
        "기존에 작성한 블로그 글을 2~5개 붙여넣고 프로필로 저장하세요. "
        "글 생성 시 이 글들의 **말투·문단 구성·형식**을 따라 씁니다. "
        "저장된 프로필은 이 앱을 쓰는 직원 모두가 공유합니다."
    )
    new_name = st.text_input("프로필 이름", placeholder="예: 회사 공식 블로그 말투")
    description = st.text_input("설명 (선택)")

    # 링크에서 원고 자동 가져오기 (네이버 블로그 공개글 등)
    st.session_state.setdefault("url_samples", [])
    with st.expander("🔗 링크에서 원고 가져오기 (직접 붙여넣기 대신)"):
        st.caption(
            "네이버 블로그/카페 글의 링크를 넣으면 본문을 자동으로 읽어옵니다. "
            "비공개·회원전용 글은 실패할 수 있어요 (그럴 땐 아래에 직접 붙여넣기)."
        )
        url = st.text_input("글 링크 (주소)", placeholder="https://blog.naver.com/...")
        if st.button("이 링크에서 원고 가져오기"):
            if not url.strip():
                st.error("링크를 입력해 주세요.")
            else:
                import extractor

                try:
                    with st.spinner("원고를 읽어오는 중... (10~20초)"):
                        text = extractor.extract_text_from_url(url)
                    st.session_state["url_samples"].append(text)
                    st.success("원고를 가져왔습니다! 아래 목록에 추가됐어요.")
                except Exception as e:
                    st.error(f"가져오기 실패: {e}")
        if st.session_state["url_samples"]:
            st.markdown("**가져온 원고 목록** (프로필 저장 시 함께 포함됩니다)")
            for i, s in enumerate(st.session_state["url_samples"]):
                st.text(f"[{i + 1}] {s[:150]}{'...' if len(s) > 150 else ''}")
            if st.button("가져온 원고 목록 비우기"):
                st.session_state["url_samples"] = []
                st.rerun()

    n = st.number_input("직접 붙여넣을 샘플 개수", min_value=0, max_value=5, value=2)
    samples_input = [
        st.text_area(f"기존 글 {i + 1}", height=150, key=f"sample_{i}") for i in range(int(n))
    ]

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("프로필 저장", type="primary", use_container_width=True):
            valid = [s for s in samples_input if s.strip()] + st.session_state["url_samples"]
            if not new_name.strip() or not valid:
                st.error("프로필 이름과 샘플 글(직접 입력 또는 링크)을 1개 이상 넣어 주세요.")
            else:
                style_store.save_profile(new_name, valid, description)
                st.session_state["url_samples"] = []
                st.success(f"'{new_name}' 프로필 저장 완료. 사이드바에서 선택하세요.")
                st.rerun()
    with col_del:
        if profiles and st.button("선택한 프로필 삭제", use_container_width=True):
            if profile_name != "(사용 안 함)":
                style_store.delete_profile(profile_name)
                st.success(f"'{profile_name}' 삭제 완료.")
                st.rerun()

    if profiles:
        st.divider()
        st.subheader("저장된 프로필")
        for name in profiles:
            data = style_store.load_profile(name)
            with st.expander(f"{name} — 샘플 {len(data['samples'])}개 (수정: {data['updated_at']})"):
                if data.get("description"):
                    st.caption(data["description"])
                for i, s in enumerate(data["samples"]):
                    st.text(f"[글 {i + 1}] {s[:200]}{'...' if len(s) > 200 else ''}")

# ---------------------------------------------------------------- 네이버 발행
with tab_publish:
    if "post" not in st.session_state:
        st.info("먼저 '글 생성' 탭에서 글을 만들어 주세요.")
    else:
        post = st.session_state["post"]
        st.markdown(f"**발행할 글:** {post['title']}")

        st.warning(
            "자동 발행은 네이버 정책 위반 소지가 있습니다. 계정 보호를 위해 "
            "**'초안만 작성'** 모드(발행 직전에 멈추고 사람이 확인 후 발행)를 권장합니다. "
            "아이디/비밀번호는 저장되지 않으며 이번 실행에만 사용됩니다."
        )

        naver_id = st.text_input("네이버 아이디")
        naver_pw = st.text_input("네이버 비밀번호", type="password")
        mode = st.radio(
            "발행 방식",
            ["초안만 작성 (권장 — 사람이 확인 후 직접 발행)", "자동 발행"],
        )

        if st.button("네이버 블로그에 작성 시작", type="primary", use_container_width=True):
            if not naver_id or not naver_pw:
                st.error("네이버 아이디와 비밀번호를 입력해 주세요.")
            else:
                import publisher  # Playwright는 필요할 때만 로드

                with st.spinner("브라우저 실행 중... 캡차/2단계 인증이 뜨면 열린 브라우저에서 직접 해결해 주세요."):
                    try:
                        result = publisher.publish_post(
                            naver_id=naver_id,
                            naver_pw=naver_pw,
                            title=post["title"],
                            body=post["body"],
                            tags=post["tags"],
                            publish=mode == "자동 발행",
                        )
                        st.success(result)
                    except Exception as e:
                        st.error(f"발행 실패: {e}")

        st.divider()
        st.markdown("**대안: 직접 붙여넣기 (가장 안전)** — 아래 내용을 복사해서 네이버 에디터에 붙여넣으세요.")
        st.code(f"{post['title']}\n\n{post['body']}\n\n{', '.join('#' + t for t in post['tags'])}")
