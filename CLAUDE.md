# 평생교육원 학사일정 공용 캘린더

여러 평생교육원의 학사일정을 회사에서 공용으로 관리·열람하는 사내 웹앱.

## 핵심 기능

1. **일정 가져오기**: 학사일정 이미지 또는 텍스트를 붙여넣으면 Claude API로 파싱해 구조화된 일정 목록 생성
2. **검수**: 파싱 결과를 편집 가능한 표로 보여주고, 사람이 수정·확인한 뒤 저장
3. **월 달력 뷰** (가장 핵심): 저장된 모든 기관의 일정을 월 단위 달력으로 표시. 회사 누구나 브라우저로 접속해 열람

## 기술 스택

| 영역 | 선택 | 이유 |
|---|---|---|
| 프레임워크 | Next.js (App Router) + TypeScript | 프론트/백엔드 단일 프로젝트, Claude API 키는 서버 Route Handler에만 존재 |
| DB | SQLite + Prisma | 사내 소규모 공용 데이터에 충분, 서버리스 파일 DB. 필요 시 Postgres로 이전 용이 |
| LLM | `@anthropic-ai/sdk`, 모델 `claude-opus-5` | 이미지(비전) 입력 + structured outputs로 스키마 검증된 JSON 파싱 |
| 검증 | Zod | 파싱 결과와 저장 API가 같은 스키마를 공유 |
| 달력 UI | 자체 월 그리드 + date-fns | 월 뷰가 핵심이므로 외부 캘린더 라이브러리 대신 CSS Grid로 직접 구현 (기관별 색상, 기간 일정 막대 등 자유로운 커스터마이징) |
| 스타일 | Tailwind CSS | 내부 도구 빠른 개발 |

- 인증: 1차 버전은 사내망 접근 전제로 생략. 필요해지면 공용 비밀번호 → SSO 순으로 추가.
- 배포: Docker 단일 컨테이너 (SQLite 파일은 볼륨 마운트).

## 폴더 구조

```
first/
├── CLAUDE.md
├── prisma/
│   └── schema.prisma          # Institution(기관), Event(일정)
├── src/
│   ├── app/
│   │   ├── page.tsx           # 메인: 월 달력 뷰
│   │   ├── import/
│   │   │   └── page.tsx       # 붙여넣기 → 파싱 → 검수 → 저장 플로우
│   │   └── api/
│   │       ├── parse/route.ts # 이미지/텍스트 → Claude 파싱 (서버 전용)
│   │       └── events/route.ts# 일정 CRUD
│   ├── components/
│   │   ├── calendar/          # MonthGrid, EventBar, MonthNavigator 등
│   │   ├── review/            # 검수 테이블 (편집 가능 행)
│   │   └── import/            # 붙여넣기 입력 영역
│   ├── lib/
│   │   ├── anthropic.ts       # SDK 클라이언트 + 파싱 프롬프트
│   │   ├── schema.ts          # Zod 스키마 (파싱 결과 = 저장 스키마)
│   │   └── db.ts              # Prisma 클라이언트
│   └── types/
└── package.json
```

## 데이터 모델 (초안)

- **Institution**: id, name, color (달력 표시 색)
- **Event**: id, institutionId, title, startDate, endDate (하루짜리면 start=end), category (개강/종강/접수/시험/휴일 등), memo, source (파싱 원본 참조)

## 개발 단계

1. **스캐폴드 + 데이터 모델**: Next.js 초기화, Prisma 스키마, 시드 데이터
2. **월 달력 뷰 (핵심 먼저)**: 시드 데이터 기반 월 그리드, 월 이동, 기관별 색상·필터
3. **일정 CRUD API + 수동 입력**: 달력이 DB를 읽고, 직접 일정 추가/수정 가능
4. **Claude 파싱 API**: 텍스트 → 이미지 순으로 지원. structured outputs + Zod 검증
5. **검수 테이블 → 저장**: 파싱 결과를 편집 가능한 표로, 확인 후 일괄 저장
6. **마무리**: 중복 일정 처리, 로딩/에러 UX, Docker 배포

## Claude API 연동 규칙

- 모델 ID는 정확히 `claude-opus-5` 사용 (날짜 접미사 붙이지 않음).
- API 호출은 반드시 서버(Route Handler)에서만. `ANTHROPIC_API_KEY`는 환경 변수로 관리, 클라이언트 번들에 노출 금지.
- 파싱 응답은 structured outputs(`output_config.format`)로 JSON 스키마를 강제하고, 서버에서 Zod로 재검증한다.
- 이미지 입력은 base64 image 콘텐츠 블록으로 전달.
- 응답의 `stop_reason` 확인 후 content를 읽는다.

## 개발 규칙

- 날짜는 DB에 ISO 8601 (`YYYY-MM-DD`) 문자열로 저장, 타임존 계산 없이 날짜 단위로만 다룬다 (학사일정은 시각 개념이 없음).
- 파싱 결과는 검수(사람 확인) 전에는 절대 DB에 저장하지 않는다.
- UI 텍스트는 한국어.
